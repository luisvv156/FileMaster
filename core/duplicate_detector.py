"""Detección de duplicados exactos y similares en archivos académicos."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from ai.text_utils import clean_text
from core.models import DocumentRecord, DuplicateGroup, DuplicateItem

logger = logging.getLogger(__name__)

# Umbral de similitud para considerar dos documentos "similares"
# 0.92 = contenido 92% igual en texto normalizado
DEFAULT_SIMILARITY_THRESHOLD = 0.92
# Máximo de caracteres a comparar (evita que SequenceMatcher sea O(n²) con textos largos)
_MAX_COMPARE_CHARS = 1500


class DuplicateDetector:
    """Detecta archivos duplicados por contenido idéntico (hash SHA-256)
    y por contenido muy similar (SequenceMatcher sobre texto normalizado).

    Uso típico desde el controller:
        detector = DuplicateDetector()
        groups, dup_ids = detector.detect(candidates, existing)
    """

    def __init__(self, similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> None:
        """
        Args:
            similarity_threshold: Ratio mínimo de similitud para marcar como duplicado.
                                  0.92 es el default (92% de contenido igual).
                                  Ajustable desde la pantalla de configuración.
        """
        self.similarity_threshold = similarity_threshold
        self._hash_cache: dict[str, str] = {}  # path → sha256

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def hash_file(self, file_path: Path) -> str:
        """Calcula el hash SHA-256 de un archivo binario.

        Usa caché en memoria para evitar recalcular archivos ya procesados
        en la misma sesión del agente.

        Args:
            file_path: Ruta del archivo a hashear.

        Returns:
            Hash SHA-256 en hexadecimal, o cadena vacía si falla.
        """
        path_str = str(file_path)

        if path_str in self._hash_cache:
            return self._hash_cache[path_str]

        try:
            digest = hashlib.sha256()
            with file_path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    digest.update(chunk)
            result = digest.hexdigest()
            self._hash_cache[path_str] = result
            return result

        except (OSError, PermissionError) as exc:
            logger.warning("No se pudo hashear '%s': %s", file_path.name, exc)
            return ""

    def detect(
        self,
        candidates: list[DocumentRecord],
        existing: list[DocumentRecord] | None = None,
    ) -> tuple[list[DuplicateGroup], set[str]]:
        """Detecta duplicados exactos y similares entre candidatos y documentos existentes.

        Primero busca duplicados exactos por SHA-256.
        Luego busca similares por SequenceMatcher en los que no sean exactos.

        Args:
            candidates: Nuevos documentos a analizar.
            existing: Documentos ya organizados (para comparación cruzada).

        Returns:
            Tupla de (lista de grupos de duplicados, set de doc_ids marcados como duplicados).
        """
        existing = existing or []
        duplicate_ids: set[str] = set()
        groups: list[DuplicateGroup] = []

        # Paso 1: duplicados exactos (O(n) con dict por hash)
        exact_groups = self._find_exact_groups(candidates, existing)
        groups.extend(exact_groups)
        for group in exact_groups:
            for item in group.items:
                if item.state == "Duplicado" and item.doc_id:
                    duplicate_ids.add(item.doc_id)

        logger.info(
            "Duplicados exactos: %d grupos (%d archivos marcados)",
            len(exact_groups), len(duplicate_ids),
        )

        # Paso 2: similares entre los que no son duplicados exactos
        remaining = [doc for doc in candidates if doc.doc_id not in duplicate_ids]
        similar_groups = self._find_similar_groups(remaining, existing)
        groups.extend(similar_groups)
        for group in similar_groups:
            for item in group.items:
                if item.state == "Duplicado" and item.doc_id:
                    duplicate_ids.add(item.doc_id)

        logger.info(
            "Duplicados similares: %d grupos adicionales",
            len(similar_groups),
        )

        return groups, duplicate_ids

    def invalidate_cache(self, file_path: Path | None = None) -> None:
        """Invalida la caché de hashes.

        Args:
            file_path: Si se pasa, solo invalida ese archivo.
                       Si None, limpia toda la caché.
        """
        if file_path:
            self._hash_cache.pop(str(file_path), None)
        else:
            self._hash_cache.clear()

    # ------------------------------------------------------------------
    # Duplicados exactos
    # ------------------------------------------------------------------

    def _find_exact_groups(
        self,
        candidates: list[DocumentRecord],
        existing: list[DocumentRecord],
    ) -> list[DuplicateGroup]:
        """Agrupa documentos con el mismo hash SHA-256."""
        by_hash: dict[str, list[DocumentRecord]] = {}

        for doc in [*existing, *candidates]:
            if not doc.hash_sha256:
                continue
            by_hash.setdefault(doc.hash_sha256, []).append(doc)

        groups: list[DuplicateGroup] = []
        for idx, docs in enumerate(
            (v for v in by_hash.values() if len(v) >= 2), start=1
        ):
            # El más reciente y grande se considera el "original" a conservar
            ordered = sorted(
                docs,
                key=lambda d: (d.modified_at, d.size_bytes),
                reverse=True,
            )
            items = [
                self._build_item(doc, is_original=(pos == 0), reason="Mismo hash SHA-256")
                for pos, doc in enumerate(ordered)
            ]
            groups.append(DuplicateGroup(
                group_id=f"exact-{idx}",
                title=f"Grupo {idx} — {len(items)} archivos",
                reason="Contenido idéntico (SHA-256)",
                items=items,
            ))
        return groups

    # ------------------------------------------------------------------
    # Duplicados similares
    # ------------------------------------------------------------------

    def _find_similar_groups(
        self,
        candidates: list[DocumentRecord],
        existing: list[DocumentRecord],
    ) -> list[DuplicateGroup]:
        """Busca pares de documentos con contenido muy similar.

        Para reducir la complejidad O(n²), primero filtra por extensión
        (no tiene sentido comparar un PDF con un DOCX) antes de calcular
        la similitud de texto.
        """
        groups: list[DuplicateGroup] = []
        already_grouped: set[str] = set()
        comparison_pool = [*existing, *candidates]
        idx = 1

        for candidate in candidates:
            if candidate.doc_id in already_grouped:
                continue

            best_match: DocumentRecord | None = None
            best_score = 0.0

            for other in comparison_pool:
                # Saltar: mismo documento, hash idéntico (ya cubierto), o ya agrupado
                if (
                    other.doc_id == candidate.doc_id
                    or other.hash_sha256 == candidate.hash_sha256
                    or other.doc_id in already_grouped
                ):
                    continue

                score = self._similarity_score(candidate, other)
                if score > best_score:
                    best_score = score
                    best_match = other

            if best_match is None or best_score < self.similarity_threshold:
                continue

            # El más reciente/grande es el original
            original, duplicate = sorted(
                [candidate, best_match],
                key=lambda d: (d.modified_at, d.size_bytes),
                reverse=True,
            )
            pct = round(best_score * 100)
            items = [
                self._build_item(original, is_original=True, reason=f"Similar {pct}%"),
                self._build_item(duplicate, is_original=False, reason=f"Similar {pct}%"),
            ]
            groups.append(DuplicateGroup(
                group_id=f"similar-{idx}",
                title=f"Grupo {idx} — 2 archivos",
                reason=f"Contenido muy similar ({pct}% — Levenshtein)",
                items=items,
            ))

            # ✅ Bug fix: marcar AMBOS doc_ids como ya agrupados
            already_grouped.add(candidate.doc_id)
            already_grouped.add(best_match.doc_id)
            idx += 1

        return groups

    # ------------------------------------------------------------------
    # Cálculo de similitud
    # ------------------------------------------------------------------

    def _similarity_score(self, left: DocumentRecord, right: DocumentRecord) -> float:
        """Calcula el ratio de similitud entre el contenido de dos documentos.

        Retorna 0.0 si las extensiones son distintas (optimización O(1)).
        Usa `clean_text` (nuevo) en lugar de `normalize_text` (viejo).

        Returns:
            Float entre 0.0 y 1.0. Valores >= similarity_threshold = duplicado.
        """
        # Filtro rápido: extensiones distintas nunca son duplicados
        if left.extension != right.extension:
            return 0.0

        left_text = clean_text(left.text) or clean_text(left.name)
        right_text = clean_text(right.text) or clean_text(right.name)

        if not left_text or not right_text:
            return 0.0

        # Limitar longitud para mantener SequenceMatcher en tiempo razonable
        return SequenceMatcher(
            None,
            left_text[:_MAX_COMPARE_CHARS],
            right_text[:_MAX_COMPARE_CHARS],
        ).ratio()

    # ------------------------------------------------------------------
    # Constructor de DuplicateItem
    # ------------------------------------------------------------------

    @staticmethod
    def _build_item(
        doc: DocumentRecord,
        is_original: bool,
        reason: str,
    ) -> DuplicateItem:
        """Construye un DuplicateItem para mostrar en la GUI."""
        modified_str = datetime.fromtimestamp(doc.modified_at).strftime("%d %b %Y")
        size_mb = round(doc.size_bytes / 1024 / 1024, 2)
        meta = f"{size_mb} MB · Modificado: {modified_str} · {doc.path}"

        return DuplicateItem(
            item_id=f"dup-{doc.doc_id}",
            doc_id=doc.doc_id,
            name=doc.name,
            current_path=doc.path,
            original_path=doc.path,
            state="Original" if is_original else "Duplicado",
            detail="" if is_original else reason,
            meta=meta,
            selected=not is_original,  # Pre-seleccionar duplicados para borrar
        )