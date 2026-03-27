"""OCR opcional usando el comando de Tesseract si esta instalado."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from core.models import ExtractionResult


class OCRHandler:
    def __init__(self) -> None:
        self._binary = shutil.which("tesseract")

    @property
    def available(self) -> bool:
        return self._binary is not None

    def extract_text(self, image_path: Path) -> ExtractionResult:
        if not self.available:
            return ExtractionResult("", "ocr", "Tesseract no esta instalado")

        try:
            result = subprocess.run(
                [self._binary, str(image_path), "stdout", "--dpi", "150"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            return ExtractionResult("", "ocr", "No fue posible ejecutar Tesseract")

        text = result.stdout.strip()
        if not text:
            return ExtractionResult("", "ocr", "No se detecto texto por OCR")
        return ExtractionResult(text, "ocr", "")
