"""Pruebas para extraccion de texto."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.text_extractor import TextExtractor


class TextExtractorTest(unittest.TestCase):
    def test_extract_reads_plain_text_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "reporte.txt"
            file_path.write_text("contenido academico de inteligencia artificial", encoding="utf-8")

            result = TextExtractor().extract(file_path)

            self.assertEqual(result.method, "plain")
            self.assertIn("inteligencia artificial", result.text)
            self.assertEqual(result.note, "")


if __name__ == "__main__":
    unittest.main()
