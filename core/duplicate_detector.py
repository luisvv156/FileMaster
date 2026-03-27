"""Deteccion de duplicados exactos y similares."""

from __future__ import annotations

import hashlib
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from ai.text_utils import normalize_text
from core.models import DocumentRecord, DuplicateGroup, DuplicateItem


class DuplicateDetector:
    def hash_file(self, file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as handler:
            for chunk in iter(lambda: handler.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def detect(
        self,
        candidates: list[DocumentRecord],
        existing: list[DocumentRecord] | None = None,
    ) -> tuple[list[DuplicateGroup], set[str]]:
        existing = existing or []
        duplicate_ids: set[str] = set()
        groups: list[DuplicateGroup] = []
        exact_groups = self._find_exact_groups(candidates, existing)
        groups.extend(exact_groups)
        for group in exact_groups:
            for item in group.items:
                if item.state == "Duplicado" and item.doc_id:
                    duplicate_ids.add(item.doc_id)

        remaining_candidates = [doc for doc in candidates if doc.doc_id not in duplicate_ids]
        similar_groups = self._find_similar_groups(remaining_candidates, existing)
        groups.extend(similar_groups)
        for group in similar_groups:
            for item in group.items:
                if item.state == "Duplicado" and item.doc_id:
                    duplicate_ids.add(item.doc_id)

        return groups, duplicate_ids

    def _find_exact_groups(
        self,
        candidates: list[DocumentRecord],
        existing: list[DocumentRecord],
    ) -> list[DuplicateGroup]:
        by_hash: dict[str, list[DocumentRecord]] = {}
        for document in [*existing, *candidates]:
            by_hash.setdefault(document.hash_sha256, []).append(document)

        groups = []
        index = 1
        for documents in by_hash.values():
            if len(documents) < 2:
                continue
            ordered = sorted(documents, key=lambda doc: (doc.modified_at, doc.size_bytes), reverse=True)
            items = [self._build_duplicate_item(document, position == 0, "Mismo hash SHA-256") for position, document in enumerate(ordered)]
            groups.append(DuplicateGroup(f"exact-{index}", f"Grupo {index} - {len(items)} archivos", "Contenido identico (MD5/SHA-256)", items))
            index += 1
        return groups

    def _find_similar_groups(
        self,
        candidates: list[DocumentRecord],
        existing: list[DocumentRecord],
    ) -> list[DuplicateGroup]:
        groups: list[DuplicateGroup] = []
        used: set[str] = set()
        index = 1
        comparison_pool = [*existing, *candidates]
        for candidate in candidates:
            if candidate.doc_id in used:
                continue
            best_match = None
            best_score = 0.0
            for other in comparison_pool:
                if other.doc_id == candidate.doc_id:
                    continue
                if other.hash_sha256 == candidate.hash_sha256:
                    continue
                score = self._similarity_score(candidate, other)
                if score > best_score:
                    best_score = score
                    best_match = other
            if best_match is None or best_score < 0.92:
                continue

            original, duplicate = sorted([candidate, best_match], key=lambda doc: (doc.modified_at, doc.size_bytes), reverse=True)
            items = [
                self._build_duplicate_item(original, True, f"Similar {round(best_score * 100)}%"),
                self._build_duplicate_item(duplicate, False, f"Similar {round(best_score * 100)}%"),
            ]
            groups.append(
                DuplicateGroup(
                    f"similar-{index}",
                    f"Grupo {index} - 2 archivos",
                    "Contenido muy similar (Levenshtein)",
                    items,
                )
            )
            used.add(candidate.doc_id)
            if duplicate.doc_id == candidate.doc_id:
                used.add(duplicate.doc_id)
            index += 1
        return groups

    def _similarity_score(self, left: DocumentRecord, right: DocumentRecord) -> float:
        if left.extension != right.extension:
            return 0.0
        left_text = normalize_text(left.text) or normalize_text(left.name)
        right_text = normalize_text(right.text) or normalize_text(right.name)
        if not left_text or not right_text:
            return 0.0
        return SequenceMatcher(None, left_text[:1200], right_text[:1200]).ratio()

    def _build_duplicate_item(self, document: DocumentRecord, original: bool, reason: str) -> DuplicateItem:
        modified = datetime.fromtimestamp(document.modified_at).strftime("%d %b %Y")
        meta = f"{round(document.size_bytes / 1024 / 1024, 2)} MB · Modificado: {modified} · {document.path}"
        return DuplicateItem(
            item_id=f"dup-{document.doc_id}",
            doc_id=document.doc_id,
            name=document.name,
            current_path=document.path,
            original_path=document.path,
            state="Original" if original else "Duplicado",
            detail="" if original else reason,
            meta=meta,
            selected=not original,
        )
