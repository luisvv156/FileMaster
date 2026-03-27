"""Pruebas para deteccion de duplicados."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai.embeddings import EmbeddingService
from core.duplicate_detector import DuplicateDetector
from core.models import DocumentRecord


class DuplicateDetectorTest(unittest.TestCase):
    def test_detect_finds_exact_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            first = base_path / "archivo_a.txt"
            second = base_path / "archivo_b.txt"
            content = "red neuronal algoritmo aprendizaje profundo"
            first.write_text(content, encoding="utf-8")
            second.write_text(content, encoding="utf-8")

            detector = DuplicateDetector()
            embedder = EmbeddingService()

            documents = [
                self._document_record(detector, embedder, first, "doc-a", content),
                self._document_record(detector, embedder, second, "doc-b", content),
            ]

            groups, duplicate_ids = detector.detect(documents)

            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0].mode, "Contenido identico (MD5/SHA-256)")
            self.assertEqual(len(duplicate_ids), 1)

    def _document_record(
        self,
        detector: DuplicateDetector,
        embedder: EmbeddingService,
        path: Path,
        doc_id: str,
        text: str,
    ) -> DocumentRecord:
        stat = path.stat()
        return DocumentRecord(
            doc_id=doc_id,
            path=str(path),
            name=path.name,
            extension=path.suffix.lower(),
            size_bytes=stat.st_size,
            modified_at=stat.st_mtime,
            text=text,
            keywords=["red", "neuronal"],
            embedding=embedder.embed(text),
            hash_sha256=detector.hash_file(path),
            extraction_method="plain",
        )


if __name__ == "__main__":
    unittest.main()
