"""Smoke test del flujo principal del controlador."""

from __future__ import annotations

import importlib
import os
import tempfile
import unittest
from pathlib import Path


class FileMasterControllerFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.app_home = self.root / "app_state"
        self.watch_dir = self.root / "watch"
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.previous_home = os.environ.get("FILEMASTER_HOME")
        os.environ["FILEMASTER_HOME"] = str(self.app_home)

        import config.settings as settings_module
        import core.controller as controller_module

        self.settings_module = importlib.reload(settings_module)
        self.controller_module = importlib.reload(controller_module)
        self.controller = self.controller_module.FileMasterController()

    def tearDown(self) -> None:
        self.controller.stop_agent()
        if self.previous_home is None:
            os.environ.pop("FILEMASTER_HOME", None)
        else:
            os.environ["FILEMASTER_HOME"] = self.previous_home

        import config.settings as settings_module
        import core.controller as controller_module

        importlib.reload(settings_module)
        importlib.reload(controller_module)
        self.temp_dir.cleanup()

    def test_full_analysis_confirmation_and_followup_organization_flow(self) -> None:
        self._write_file("ia_doc_1.txt", "red neuronal algoritmo aprendizaje profundo")
        self._write_file("ia_doc_2.txt", "red neuronal algoritmo aprendizaje profundo")
        self._write_file("bd_doc_1.txt", "consulta sql joins normalizacion tablas relacionales")

        self.controller.update_config(str(self.watch_dir), auto_rename=True, detect_duplicates=True)
        proposals = self.controller.analyze_initial()

        self.assertEqual(len(proposals), 2)

        mapping = {proposal["group_id"]: proposal["suggested_name"] for proposal in proposals}
        summary = self.controller.confirm_groups(mapping)

        self.assertEqual(summary["organized"], 2)
        self.assertEqual(summary["duplicates"], 1)
        self.assertTrue((self.watch_dir / "_Duplicados").exists())
        self.assertTrue(any((self.watch_dir / "Inteligencia Artificial").iterdir()))
        self.assertTrue(any((self.watch_dir / "Base de Datos").iterdir()))

        self.controller.stop_agent()
        self._write_file("ia_doc_3.txt", "modelo de aprendizaje profundo con red neuronal artificial")

        followup = self.controller.organize_now()

        self.assertEqual(followup["organized"], 1)
        self.assertEqual(followup["unclassified"], 0)
        self.assertTrue(any((self.watch_dir / "Inteligencia Artificial").iterdir()))
        self.assertEqual(self.settings_module.APP_STATE_DIR, self.app_home)

    def _write_file(self, name: str, content: str) -> None:
        (self.watch_dir / name).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
