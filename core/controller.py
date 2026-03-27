"""Controlador principal de FileMaster."""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from ai.classifier import DocumentClassifier
from ai.clustering import DocumentClusterer
from ai.embeddings import EmbeddingService, centroid
from ai.keyword_extractor import KeywordExtractor
from ai.text_utils import title_from_keywords
from config.settings import (
    DEFAULT_DUPLICATES_FOLDER_NAME,
    HISTORY_DB_PATH,
    UserConfig,
    ensure_data_files,
    load_categories,
    load_runtime_state,
    load_user_config,
    save_categories,
    save_runtime_state,
    save_user_config,
)
from core.duplicate_detector import DuplicateDetector
from core.file_manager import FileManager
from core.history import HistoryRecord, HistoryRepository
from core.models import CategoryProfile, CycleSummary, DocumentRecord, DuplicateGroup, GroupProposal
from core.organizer import Organizer
from core.text_extractor import TextExtractor
from core.watcher import FileWatcher


KNOWN_CATEGORY_HINTS = {
    "Inteligencia Artificial": {"red", "neuronal", "algoritmo", "clasificacion", "aprendizaje", "modelo", "ia"},
    "Redes de Computadoras": {"router", "switch", "tcp", "ip", "latencia", "protocolo", "firewall"},
    "Base de Datos": {"sql", "consulta", "joins", "indice", "normalizacion", "tabla", "relacional"},
    "Sistemas Operativos": {"kernel", "memoria", "proceso", "scheduler", "hilo", "sistema"},
}

logger = logging.getLogger(__name__)


class FileMasterController:
    def __init__(self, notify_callback=None) -> None:
        ensure_data_files()
        self.notify_callback = notify_callback
        self.config = load_user_config()
        self.file_manager = FileManager()
        self.text_extractor = TextExtractor()
        self.embedder = EmbeddingService()
        self.keyword_extractor = KeywordExtractor()
        self.clusterer = DocumentClusterer()
        self.classifier = DocumentClassifier()
        self.duplicate_detector = DuplicateDetector()
        self.organizer = Organizer(self.file_manager)
        self.history = HistoryRepository(HISTORY_DB_PATH)
        self._busy = threading.Lock()
        self._pending_documents: list[DocumentRecord] = []
        self.state = self._build_initial_state()
        self.watcher = FileWatcher(self._handle_watcher_event)
        self._bootstrap()

    def _build_initial_state(self) -> dict[str, object]:
        persisted = load_runtime_state()
        return {
            "config": asdict(self.config),
            "pending_groups": persisted.get("pending_groups", []),
            "categories": load_categories(),
            "recent_files": [],
            "duplicate_groups": persisted.get("duplicate_groups", []),
            "unclassified": persisted.get("unclassified", []),
            "last_summary": persisted.get("last_summary", {}),
            "agent": {
                "active": False,
                "paused": False,
                "started_at": persisted.get("agent_started_at", ""),
                "last_run": persisted.get("last_run", ""),
            },
            "status_message": "",
        }

    def _bootstrap(self) -> None:
        self.refresh_runtime_state()
        if self.config.watch_path and self.config.watch_path.exists():
            self.start_agent()

    def snapshot(self) -> dict[str, object]:
        return json.loads(json.dumps(self.state, ensure_ascii=False))

    def has_configuration(self) -> bool:
        return self.config.is_configured and self.config.watch_path is not None and self.config.watch_path.exists()

    def update_config(self, watch_folder: str, auto_rename: bool, detect_duplicates: bool) -> None:
        clean_watch_folder = watch_folder.strip()
        folder_changed = self.config.watch_folder.strip() != clean_watch_folder
        if folder_changed:
            self.stop_agent()
            self._reset_workspace_state()

        self.config = UserConfig(
            watch_folder=clean_watch_folder,
            auto_rename=auto_rename,
            detect_duplicates=detect_duplicates,
            similarity_threshold=self.config.similarity_threshold,
        )
        save_user_config(self.config)
        self.state["config"] = asdict(self.config)
        self.state["status_message"] = (
            "Configuracion actualizada. Ejecuta un analisis inicial para confirmar los grupos sugeridos."
            if folder_changed
            else "Configuracion actualizada."
        )
        self.refresh_runtime_state()
        logger.info(
            "Configuracion actualizada | carpeta=%s | auto_rename=%s | detect_duplicates=%s | folder_changed=%s",
            self.config.watch_folder,
            self.config.auto_rename,
            self.config.detect_duplicates,
            folder_changed,
        )
        self._notify()

    def analyze_initial(self) -> list[dict[str, object]]:
        watch_path = self._require_watch_folder()
        documents = self._collect_documents(self._incoming_files(watch_path))
        if not documents:
            self._pending_documents = []
            self.state["pending_groups"] = []
            self.state["status_message"] = "No se encontraron archivos nuevos para analizar."
            self._persist_runtime()
            self._notify()
            logger.info("Analisis inicial sin archivos nuevos | carpeta=%s", watch_path)
            return []

        labels = self.clusterer.cluster([document.embedding for document in documents])
        grouped_documents: dict[int, list[DocumentRecord]] = defaultdict(list)
        for label, document in zip(labels, documents):
            grouped_documents[label].append(document)

        proposals: list[GroupProposal] = []
        for index, documents_in_group in enumerate(grouped_documents.values(), start=1):
            keywords = self._keywords_for_documents(documents_in_group)
            name = self._suggest_category_name(keywords)
            proposals.append(
                GroupProposal(
                    group_id=f"group-{index}",
                    suggested_name=name,
                    keywords=keywords,
                    file_ids=[document.doc_id for document in documents_in_group],
                    file_names=[document.name for document in documents_in_group],
                )
            )

        self.state["pending_groups"] = [asdict(proposal) for proposal in proposals]
        self._pending_documents = documents
        self.state["status_message"] = f"Se detectaron {len(proposals)} grupos para confirmar."
        self._persist_runtime()
        logger.info("Analisis inicial completado | carpeta=%s | grupos=%s | documentos=%s", watch_path, len(proposals), len(documents))
        self._notify()
        return self.state["pending_groups"]

    def confirm_groups(self, mapping: dict[str, str]) -> dict[str, object]:
        pending_groups = self.state.get("pending_groups", [])
        if not pending_groups:
            return {}

        proposals = {group["group_id"]: group for group in pending_groups}
        documents = list(self._pending_documents)
        if not documents:
            return {}

        group_assignments: dict[str, str] = {}
        categories_payload = []
        for group_id, group in proposals.items():
            name = (mapping.get(group_id) or group["suggested_name"]).strip() or group["suggested_name"]
            group_assignments[group_id] = name
            categories_payload.append(
                {
                    "name": name,
                    "keywords": group["keywords"],
                    "files": group["file_names"],
                }
            )

        save_categories(categories_payload)
        self.state["categories"] = categories_payload

        assignment_by_doc: dict[str, str] = {}
        for group in pending_groups:
            for document_id in group["file_ids"]:
                assignment_by_doc[document_id] = group_assignments[group["group_id"]]

        for document in documents:
            document.assigned_category = assignment_by_doc.get(document.doc_id)

        summary = self._organize_documents(documents, explicit_assignments=assignment_by_doc)
        self._pending_documents = []
        self.state["pending_groups"] = []
        self.refresh_runtime_state(last_summary=summary)
        self.start_agent()
        logger.info("Grupos confirmados | categorias=%s | organizados=%s", len(categories_payload), summary.get("organized", 0))
        self._notify()
        return summary

    def organize_now(self) -> dict[str, object]:
        watch_path = self._require_watch_folder()
        if not load_categories():
            proposals = self.analyze_initial()
            if proposals:
                self.state["status_message"] = "Se detectaron documentos nuevos. Confirma los grupos sugeridos para continuar."
                self._notify()
                logger.info("Organizacion detenida a la espera de confirmacion de grupos | grupos=%s", len(proposals))
                return self._empty_summary()
        incoming = self._collect_documents(self._incoming_files(watch_path))
        if not incoming:
            self.state["status_message"] = "No hay archivos nuevos para organizar."
            self._notify()
            logger.info("Organizacion manual sin archivos nuevos | carpeta=%s", watch_path)
            return self.state.get("last_summary", {})

        summary = self._organize_documents(incoming)
        self.refresh_runtime_state(last_summary=summary)
        logger.info(
            "Organizacion manual completada | detectados=%s | organizados=%s | duplicados=%s | sin_clasificar=%s",
            summary.get("detected", 0),
            summary.get("organized", 0),
            summary.get("duplicates", 0),
            summary.get("unclassified", 0),
        )
        self._notify()
        return summary

    def toggle_agent(self) -> None:
        if not self.watcher.is_running:
            self.start_agent()
            return
        if self.watcher.paused:
            self.watcher.resume()
            self.state["agent"]["paused"] = False
            self.state["status_message"] = "El agente reanudo el monitoreo."
        else:
            self.watcher.pause()
            self.state["agent"]["paused"] = True
            self.state["status_message"] = "El agente se encuentra en pausa."
        self._persist_runtime()
        logger.info("Cambio de estado del agente | activo=%s | pausado=%s", self.watcher.is_running, self.watcher.paused)
        self._notify()

    def start_agent(self) -> None:
        if not self.has_configuration():
            return
        watch_path = self._require_watch_folder()
        self.file_manager.ensure_folder(watch_path / DEFAULT_DUPLICATES_FOLDER_NAME)
        self.watcher.start(watch_path)
        self.state["agent"]["active"] = True
        self.state["agent"]["paused"] = False
        self.state["agent"]["started_at"] = datetime.now().strftime("%H:%M:%S")
        self._persist_runtime()
        logger.info("Agente iniciado | carpeta=%s", watch_path)

    def stop_agent(self) -> None:
        self.watcher.stop()
        self.state["agent"]["active"] = False
        self.state["agent"]["paused"] = False
        self._persist_runtime()
        logger.info("Agente detenido")
        self._notify()

    def manual_categories(self) -> list[str]:
        categories = self.state.get("categories", [])
        return [category["name"] for category in categories]

    def create_category(self, name: str) -> None:
        clean_name = name.strip()
        if not clean_name:
            return
        categories = load_categories()
        if all(category["name"] != clean_name for category in categories):
            categories.append({"name": clean_name, "keywords": [], "files": []})
            save_categories(categories)
            self.state["categories"] = categories

    def manual_classify(self, file_path: str, category_name: str, new_folder_name: str = "") -> None:
        if new_folder_name.strip():
            self.create_category(new_folder_name.strip())
            category_name = new_folder_name.strip()

        path = Path(file_path)
        if not path.exists():
            return

        documents = self._collect_documents([path])
        if not documents:
            self.state["status_message"] = f"No fue posible procesar {path.name} para clasificarlo manualmente."
            self._notify()
            return

        document = documents[0]
        destination = self.organizer.organize(
            path,
            self._require_watch_folder(),
            category_name,
            auto_rename=self.config.auto_rename,
            keywords=document.keywords,
        )
        self.history.add_record(
            HistoryRecord(
                source=str(path),
                destination=str(destination),
                action="manual_classified",
                category=category_name,
                confidence=1.0,
            )
        )
        self.state["status_message"] = f"{path.name} fue movido manualmente a {category_name}."
        self.refresh_runtime_state()
        logger.info("Archivo clasificado manualmente | archivo=%s | categoria=%s", path, category_name)
        self._notify()

    def delete_duplicates(self, selected_paths: list[str]) -> None:
        removed = 0
        for path_str in selected_paths:
            path = Path(path_str)
            if path.exists():
                self.file_manager.delete_file(path)
                removed += 1
                self.history.add_record(
                    HistoryRecord(source=path_str, destination="", action="duplicate_deleted", category="")
                )
        self.state["status_message"] = f"Se eliminaron {removed} archivos duplicados."
        self.refresh_runtime_state()
        logger.info("Duplicados eliminados | cantidad=%s", removed)
        self._notify()

    def restore_duplicates(self, selected_paths: list[str]) -> None:
        restored = 0
        for path_str in selected_paths:
            source = Path(path_str)
            if not source.exists():
                continue
            original_path = self._original_duplicate_path(path_str)
            destination = self.file_manager.move_file(source, original_path or (self._require_watch_folder() / source.name))
            restored += 1
            self.history.add_record(
                HistoryRecord(source=path_str, destination=str(destination), action="duplicate_restored", category="")
            )
        self.state["status_message"] = f"Se restauraron {restored} archivos al directorio principal."
        self.refresh_runtime_state()
        logger.info("Duplicados restaurados | cantidad=%s", restored)
        self._notify()

    def refresh_runtime_state(self, last_summary: dict[str, object] | None = None) -> None:
        stats = self.history.overall_stats()
        recent_records = self.history.recent_records(limit=6)
        self.state["recent_files"] = self._format_recent_records(recent_records)
        self.state["categories"] = load_categories()
        self.state["duplicate_groups"] = self._load_duplicate_groups_from_runtime()
        self.state["unclassified"] = self._scan_unclassified()
        if last_summary is not None:
            self.state["last_summary"] = last_summary
        elif not self.state.get("last_summary"):
            self.state["last_summary"] = self._empty_summary()

        self.state["stats"] = {
            "total_organized": int(stats["total_organized"]),
            "duplicates_detected": int(stats["duplicates_detected"]),
            "average_confidence": round(stats["average_confidence"] * 100, 1),
            "folders_created": len(self.state["categories"]),
        }
        self.state["config"] = asdict(self.config)
        self._persist_runtime()

    def _collect_documents(self, file_paths: list[Path]) -> list[DocumentRecord]:
        documents = []
        for file_path in file_paths:
            if not file_path.exists() or not file_path.is_file():
                continue
            extraction = self.text_extractor.extract(file_path)
            keywords = self.keyword_extractor.extract(extraction.text or file_path.stem)
            embedding = self.embedder.embed(extraction.text or " ".join(keywords) or file_path.stem)
            try:
                digest = self.duplicate_detector.hash_file(file_path)
            except OSError:
                continue
            stat = file_path.stat()
            documents.append(
                DocumentRecord(
                    doc_id=uuid.uuid4().hex,
                    path=str(file_path),
                    name=file_path.name,
                    extension=file_path.suffix.lower(),
                    size_bytes=stat.st_size,
                    modified_at=stat.st_mtime,
                    text=extraction.text,
                    keywords=keywords,
                    embedding=embedding,
                    hash_sha256=digest,
                    extraction_method=extraction.method,
                    extraction_note=extraction.note,
                )
            )
        return documents

    def _organize_documents(
        self,
        documents: list[DocumentRecord],
        *,
        explicit_assignments: dict[str, str] | None = None,
    ) -> dict[str, object]:
        start = time.perf_counter()
        explicit_assignments = explicit_assignments or {}
        watch_path = self._require_watch_folder()
        duplicates_folder = watch_path / DEFAULT_DUPLICATES_FOLDER_NAME
        existing = self._collect_documents(self._managed_files(watch_path))

        duplicate_groups, duplicate_ids = self.duplicate_detector.detect(
            documents,
            existing if self.config.detect_duplicates else [],
        )

        categories = self._build_category_profiles(existing, load_categories())
        cycle = CycleSummary(detected=len(documents))
        folder_counter: Counter[str] = Counter()
        confidence_values: list[float] = []
        persisted_duplicate_groups = []
        unclassified_notes = []

        for group in duplicate_groups:
            persisted_duplicate_groups.append(asdict(group))

        for document in documents:
            source = Path(document.path)
            if document.doc_id in duplicate_ids:
                duplicate_path = self.organizer.move_to_duplicates(source, duplicates_folder)
                self._update_duplicate_item_path(persisted_duplicate_groups, document.doc_id, duplicate_path, Path(document.path))
                cycle.duplicates += 1
                self.history.add_record(
                    HistoryRecord(
                        source=document.path,
                        destination=str(duplicate_path),
                        action="duplicate_moved",
                        category="",
                        confidence=1.0,
                    )
                )
                continue

            assigned = explicit_assignments.get(document.doc_id)
            confidence = 1.0 if assigned else 0.0
            if not assigned:
                label, confidence = self.classifier.classify(
                    document.embedding,
                    {category.name: category.centroid for category in categories if category.centroid},
                    similarity_threshold=self.config.similarity_threshold,
                )
                assigned = label
                if not assigned:
                    assigned, confidence = self._classify_by_keywords(document.keywords, categories)

            if not assigned or not (document.text.strip() or document.keywords):
                cycle.unclassified += 1
                unclassified_notes.append(
                    {
                        "path": document.path,
                        "name": document.name,
                        "reason": document.extraction_note or "No se encontro texto suficiente para clasificarlo.",
                        "keywords": document.keywords,
                    }
                )
                continue

            destination = self.organizer.organize(
                source,
                watch_path,
                assigned,
                auto_rename=self.config.auto_rename,
                keywords=document.keywords,
            )
            self._update_duplicate_item_path(persisted_duplicate_groups, document.doc_id, destination, Path(document.path))
            folder_counter[assigned] += 1
            cycle.organized += 1
            if destination.name != source.name:
                cycle.renamed += 1
            confidence_values.append(confidence or 1.0)
            self.history.add_record(
                HistoryRecord(
                    source=document.path,
                    destination=str(destination),
                    action="organized",
                    category=assigned,
                    confidence=confidence or 1.0,
                    details=json.dumps({"keywords": document.keywords}, ensure_ascii=False),
                )
            )

        cycle.precision = round((sum(confidence_values) / len(confidence_values)) * 100, 1) if confidence_values else 0.0
        cycle.duration_seconds = round(time.perf_counter() - start, 2)
        cycle.folders = [
            {"name": name, "count": count, "path": str(watch_path / name)}
            for name, count in sorted(folder_counter.items())
        ]

        summary = asdict(cycle)
        self.state["duplicate_groups"] = persisted_duplicate_groups
        self.state["unclassified"] = unclassified_notes
        self.state["last_summary"] = summary
        self.state["status_message"] = "Organizacion completada."
        self.state["agent"]["last_run"] = datetime.now().strftime("%H:%M:%S")
        self._persist_runtime()
        return summary

    def _build_category_profiles(
        self,
        managed_documents: list[DocumentRecord],
        persisted_categories: list[dict[str, object]],
    ) -> list[CategoryProfile]:
        by_name: dict[str, list[DocumentRecord]] = defaultdict(list)
        watch_path = self._require_watch_folder()
        for document in managed_documents:
            path = Path(document.path)
            if path.parent == watch_path:
                continue
            if path.parent.name == DEFAULT_DUPLICATES_FOLDER_NAME:
                continue
            by_name[path.parent.name].append(document)

        categories: list[CategoryProfile] = []
        for item in persisted_categories:
            name = str(item["name"])
            documents = by_name.get(name, [])
            keywords = self._keywords_for_documents(documents) or list(item.get("keywords", []))
            vectors = [document.embedding for document in documents if document.embedding]
            categories.append(
                CategoryProfile(
                    name=name,
                    keywords=keywords,
                    centroid=centroid(vectors) if vectors else [],
                    files=[document.path for document in documents],
                )
            )
        return categories

    def _keywords_for_documents(self, documents: list[DocumentRecord], limit: int = 5) -> list[str]:
        counter: Counter[str] = Counter()
        for document in documents:
            counter.update(document.keywords)
        return [token for token, _count in counter.most_common(limit)]

    def _suggest_category_name(self, keywords: list[str]) -> str:
        keyword_set = set(keywords)
        for name, hints in KNOWN_CATEGORY_HINTS.items():
            if keyword_set.intersection(hints):
                return name
        return title_from_keywords(keywords, fallback="Grupo Academico")

    def _classify_by_keywords(
        self,
        document_keywords: list[str],
        categories: list[CategoryProfile],
    ) -> tuple[str | None, float]:
        document_set = set(document_keywords)
        best_name = None
        best_score = 0.0
        if not document_set:
            return None, 0.0

        for category in categories:
            category_set = set(category.keywords)
            if not category_set:
                continue
            intersection = len(document_set.intersection(category_set))
            union = len(document_set.union(category_set))
            score = intersection / union if union else 0.0
            if score > best_score:
                best_name = category.name
                best_score = score

        if best_name and best_score >= 0.18:
            return best_name, best_score
        return None, best_score

    def _incoming_files(self, watch_path: Path) -> list[Path]:
        if not watch_path.exists():
            return []
        return [child for child in watch_path.iterdir() if child.is_file()]

    def _managed_files(self, watch_path: Path) -> list[Path]:
        files = []
        if not watch_path.exists():
            return files
        for category in load_categories():
            folder = watch_path / category["name"]
            if folder.exists():
                files.extend(child for child in folder.iterdir() if child.is_file())
        return files

    def _scan_unclassified(self) -> list[dict[str, object]]:
        if not self.has_configuration():
            return []
        watch_path = self._require_watch_folder()
        documents = self._collect_documents(self._incoming_files(watch_path))
        return [
            {
                "path": document.path,
                "name": document.name,
                "reason": document.extraction_note or "No fue posible determinar una categoria automaticamente.",
                "keywords": document.keywords,
                "meta": f"{round(document.size_bytes / 1024, 1)} KB · {document.extension or 'archivo'}",
            }
            for document in documents
        ]

    def _format_recent_records(self, records: list[dict[str, object]]) -> list[dict[str, object]]:
        recent = []
        for record in records:
            if record["action"] not in {"organized", "manual_classified"}:
                continue
            source_name = Path(record["source"]).name
            destination_name = Path(record["destination"]).name
            timestamp = datetime.fromisoformat(record["timestamp"])
            recent.append(
                {
                    "name": destination_name,
                    "original": f"Origen: {source_name}",
                    "category": record["category"] or "General",
                    "time": timestamp.strftime("%d %b %H:%M"),
                }
            )
        return recent

    def _empty_summary(self) -> dict[str, object]:
        return asdict(CycleSummary())

    def _load_duplicate_groups_from_runtime(self) -> list[dict[str, object]]:
        persisted = load_runtime_state()
        return self._prune_duplicate_groups(persisted.get("duplicate_groups", []))

    def _prune_duplicate_groups(self, groups: list[dict[str, object]]) -> list[dict[str, object]]:
        clean_groups = []
        for group in groups:
            items = []
            for item in group.get("items", []):
                current_path = item.get("current_path", "")
                if not current_path or not Path(current_path).exists():
                    continue
                items.append(item)
            if len(items) < 2:
                continue
            if not any(item.get("state") == "Duplicado" for item in items):
                continue
            clean_group = dict(group)
            clean_group["items"] = items
            clean_groups.append(clean_group)
        return clean_groups

    def _reset_workspace_state(self) -> None:
        empty_summary = self._empty_summary()
        save_categories([])
        self._pending_documents = []
        self.state["pending_groups"] = []
        self.state["categories"] = []
        self.state["duplicate_groups"] = []
        self.state["unclassified"] = []
        self.state["last_summary"] = empty_summary
        self.state["agent"]["started_at"] = ""
        self.state["agent"]["last_run"] = ""
        save_runtime_state(
            {
                "pending_groups": [],
                "duplicate_groups": [],
                "unclassified": [],
                "last_summary": empty_summary,
                "agent_started_at": "",
                "last_run": "",
            }
        )

    def _update_duplicate_item_path(
        self,
        duplicate_groups: list[dict[str, object]],
        doc_id: str,
        current_path: Path,
        original_path: Path,
    ) -> None:
        for group in duplicate_groups:
            for item in group.get("items", []):
                if item.get("doc_id") != doc_id:
                    continue
                item["current_path"] = str(current_path)
                item["original_path"] = str(original_path)
                meta = item.get("meta", "")
                if "·" in meta:
                    parts = meta.split("·")
                    item["meta"] = "·".join(parts[:-1] + [f" {current_path}"])
                else:
                    item["meta"] = f"{current_path}"

    def _original_duplicate_path(self, current_path: str) -> Path | None:
        for group in self.state.get("duplicate_groups", []):
            for item in group.get("items", []):
                if item.get("current_path") == current_path:
                    original = item.get("original_path")
                    if original:
                        return Path(original)
        return None

    def _persist_runtime(self) -> None:
        payload = {
            "pending_groups": self.state.get("pending_groups", []),
            "duplicate_groups": self.state.get("duplicate_groups", []),
            "unclassified": self.state.get("unclassified", []),
            "last_summary": self.state.get("last_summary", {}),
            "agent_started_at": self.state["agent"].get("started_at", ""),
            "last_run": self.state["agent"].get("last_run", ""),
        }
        save_runtime_state(payload)

    def _handle_watcher_event(self) -> None:
        if not self._busy.acquire(blocking=False):
            return
        try:
            self.organize_now()
        except Exception:
            logger.exception("Error durante la ejecucion del watcher")
        finally:
            self._busy.release()

    def _require_watch_folder(self) -> Path:
        watch_path = self.config.watch_path
        if watch_path is None:
            raise ValueError("La carpeta monitoreada no ha sido configurada.")
        self.file_manager.ensure_folder(watch_path)
        return watch_path

    def _notify(self) -> None:
        if self.notify_callback:
            self.notify_callback()
