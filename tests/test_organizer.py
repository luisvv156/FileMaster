"""Pruebas para movimiento y renombrado de archivos."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.organizer import Organizer


class OrganizerTest(unittest.TestCase):
    def test_organize_moves_file_to_category_folder_and_renames_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "SKDJH-KEFHE.pdf"
            source.write_text("contenido de inteligencia artificial", encoding="utf-8")

            destination = Organizer().organize(
                source,
                root,
                "Inteligencia Artificial",
                auto_rename=True,
                keywords=["reporte", "clasificacion"],
            )

            self.assertTrue(destination.exists())
            self.assertFalse(source.exists())
            self.assertEqual(destination.parent.name, "Inteligencia Artificial")
            self.assertTrue(destination.name.startswith("inteligencia_artificial_reporte_clasificacion_"))


if __name__ == "__main__":
    unittest.main()
