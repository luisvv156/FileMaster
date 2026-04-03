"""OCR opcional usando Tesseract si está instalado en el sistema.

Soporta documentos escaneados (JPG, PNG, TIFF) y páginas de PDF
que requieran reconocimiento óptico de caracteres.

Requisito externo: Tesseract OCR (https://github.com/UB-Mannheim/tesseract/wiki)
    Windows: Instalar el ejecutable + agregar al PATH
    Idiomas recomendados: spa (español) + eng (inglés)
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from core.models import ExtractionResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
DEFAULT_DPI = 300           # Resolución estándar para documentos académicos
DEFAULT_LANGS = "spa+eng"   # Español + inglés (los más comunes en el contexto del proyecto)
OCR_TIMEOUT = 60            # Segundos antes de cancelar (documentos grandes pueden tardar)

# Modos de segmentación de página de Tesseract
# 3 = Segmentación automática (default, buena para documentos normales)
# 6 = Asume bloque de texto uniforme (bueno para PDFs con layout simple)
PSM_AUTO = "3"
PSM_BLOCK = "6"


class OCRHandler:
    """Wrapper sobre Tesseract OCR para extracción de texto desde imágenes.

    Uso típico (desde text_extractor.py):
        handler = OCRHandler()
        if handler.available:
            result = handler.extract_text(Path("escaneo.jpg"))
            print(result.text)
    """

    def __init__(
        self,
        languages: str = DEFAULT_LANGS,
        dpi: int = DEFAULT_DPI,
        psm: str = PSM_AUTO,
    ) -> None:
        """
        Args:
            languages: Idiomas de Tesseract separados por '+'. Ej: "spa+eng"
            dpi: Resolución en DPI para el procesamiento de imagen.
            psm: Page Segmentation Mode de Tesseract (3=auto, 6=bloque uniforme).
        """
        self._binary: str | None = self._find_tesseract()
        self.languages = languages
        self.dpi = dpi
        self.psm = psm

        if self._binary:
            logger.debug("Tesseract encontrado en: %s", self._binary)
        else:
            logger.warning(
                "Tesseract no encontrado en PATH. "
                "OCR no disponible. Instalar desde: "
                "https://github.com/UB-Mannheim/tesseract/wiki"
            )

    # ------------------------------------------------------------------
    # Propiedades públicas
    # ------------------------------------------------------------------

    @staticmethod
    def _find_tesseract() -> str | None:
        """Busca tesseract en PATH y en rutas comunes de Windows."""
        # Intentar primero con PATH normal
        found = shutil.which("tesseract")
        if found:
            return found

        # Rutas comunes de instalación en Windows
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\tugfa\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
        ]
        for path in common_paths:
            if Path(path).exists():
                return path

        return None

    @property
    def available(self) -> bool:
        """True si Tesseract está instalado y localizable en el PATH."""
        return self._binary is not None

    @property
    def version(self) -> str | None:
        """Retorna la versión de Tesseract instalada, o None si no está disponible."""
        if not self.available:
            return None
        try:
            result = subprocess.run(
                [self._binary, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            first_line = (result.stdout or result.stderr).splitlines()[0]
            return first_line.strip()
        except (OSError, subprocess.SubprocessError, IndexError):
            return None

    # ------------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------------

    def extract_text(self, image_path: Path, *, psm: str | None = None) -> ExtractionResult:
        """Extrae texto de una imagen mediante OCR.

        Args:
            image_path: Ruta a la imagen (JPG, PNG, TIFF, BMP).
            psm: Page Segmentation Mode override para esta imagen específica.
                 None usa el valor configurado en __init__.

        Returns:
            ExtractionResult con el texto extraído o un mensaje de error.
        """
        if not self.available:
            return ExtractionResult("", "ocr", "Tesseract no está instalado")

        if not image_path.exists():
            return ExtractionResult(
                "", "ocr", f"Imagen no encontrada: {image_path.name}"
            )

        effective_psm = psm or self.psm

        cmd = [
            self._binary,
            str(image_path),   # input
            "stdout",          # output a stdout en lugar de archivo
            "--dpi", str(self.dpi),
            "-l", self.languages,
            "--psm", effective_psm,
            "--oem", "3",      # OEM 3 = LSTM + legado (mejor precisión)
        ]

        logger.debug(
            "Ejecutando OCR: %s (dpi=%d, lang=%s, psm=%s)",
            image_path.name, self.dpi, self.languages, effective_psm,
        )

        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=OCR_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warning("OCR timeout para: %s", image_path.name)
            return ExtractionResult("", "ocr", f"Timeout al procesar {image_path.name}")
        except (OSError, subprocess.SubprocessError) as exc:
            logger.error("Error al ejecutar Tesseract para '%s': %s", image_path.name, exc)
            return ExtractionResult("", "ocr", f"Error al ejecutar Tesseract: {exc}")

        # Tesseract usa returncode != 0 para errores reales
        if result.returncode != 0:
            stderr_msg = result.stderr.strip()
            logger.warning(
                "Tesseract retornó código %d para '%s': %s",
                result.returncode, image_path.name, stderr_msg,
            )
            # Returncode 1 a veces es solo advertencia de idioma, no error fatal
            # Si hay texto en stdout de todas formas, lo aceptamos
            if not result.stdout.strip():
                return ExtractionResult(
                    "", "ocr",
                    f"Tesseract falló (código {result.returncode}): {stderr_msg[:100]}"
                )

        text = result.stdout.strip()

        if not text:
            logger.debug("OCR sin resultado para: %s", image_path.name)
            return ExtractionResult("", "ocr", "No se detectó texto en la imagen")

        logger.info(
            "OCR exitoso: '%s' → %d caracteres extraídos",
            image_path.name, len(text),
        )
        return ExtractionResult(text, "ocr", "")

    def is_language_installed(self, lang_code: str) -> bool:
        """Verifica si un idioma específico está instalado en Tesseract.

        Útil para dar feedback en la GUI de configuración si el usuario
        no tiene los paquetes de idioma instalados.

        Args:
            lang_code: Código de idioma, ej: "spa", "eng", "fra"

        Returns:
            True si el idioma está disponible.
        """
        if not self.available:
            return False
        try:
            result = subprocess.run(
                [self._binary, "--list-langs"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            installed = (result.stdout + result.stderr).lower()
            return lang_code.lower() in installed
        except (OSError, subprocess.SubprocessError):
            return False