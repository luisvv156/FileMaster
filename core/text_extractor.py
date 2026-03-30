"""Extracción de texto para los formatos soportados por FileMaster.

Jerarquía de extracción por formato:
  PDF   → PyMuPDF (fitz) → pdftotext CLI → regex básico → OCR
  DOCX  → python-docx → XML manual (fallback)
  PPTX  → python-pptx → XML manual (fallback)
  Texto → lectura directa con detección de encoding
  Imagen → OCR (Tesseract vía OCRHandler)
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from config.settings import IMAGE_EXTENSIONS
from core.models import ExtractionResult
from core.ocr_handler import OCRHandler

logger = logging.getLogger(__name__)

# Límite de caracteres para no saturar el pipeline NLP/embeddings
MAX_CHARS = 50_000

# Encodings a probar en orden para archivos de texto plano
_TEXT_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1")


class TextExtractor:
    """Extrae texto de documentos en múltiples formatos.

    Usa las bibliotecas de mayor calidad disponibles y degrada
    graciosamente si alguna no está instalada.
    """

    def __init__(self) -> None:
        self.ocr_handler = OCRHandler()
        self._pdftotext = shutil.which("pdftotext")
        self._has_fitz = self._check_import("fitz")
        self._has_docx = self._check_import("docx")
        self._has_pptx = self._check_import("pptx")

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

    def extract(self, file_path: Path) -> ExtractionResult:
        """Extrae texto del archivo según su extensión.

        Args:
            file_path: Ruta al archivo a procesar.

        Returns:
            ExtractionResult con el texto extraído, método usado y
            mensaje de error (vacío si todo fue bien).
        """
        if not file_path.exists():
            return ExtractionResult("", "error", f"Archivo no encontrado: {file_path}")

        suffix = file_path.suffix.lower()

        extractors = {
            ".pdf": self._extract_pdf,
            ".docx": self._extract_docx,
            ".pptx": self._extract_pptx,
            ".doc": self._extract_doc_fallback,
        }

        plain_text_extensions = {
            ".txt", ".md", ".csv", ".json", ".log",
            ".py", ".js", ".html", ".xml", ".rst",
        }

        if suffix in plain_text_extensions:
            result = self._extract_plain_text(file_path)
        elif suffix in extractors:
            result = extractors[suffix](file_path)
        elif suffix in IMAGE_EXTENSIONS:
            result = self.ocr_handler.extract_text(file_path)
        else:
            return ExtractionResult("", "unsupported", f"Formato no soportado: {suffix}")

        # Truncar para no saturar el pipeline NLP
        if len(result.text) > MAX_CHARS:
            logger.debug("Texto truncado de %d a %d caracteres en %s",
                         len(result.text), MAX_CHARS, file_path.name)
            result = ExtractionResult(result.text[:MAX_CHARS], result.method, result.error)

        return result

    # ------------------------------------------------------------------
    # Extractores por formato
    # ------------------------------------------------------------------

    def _extract_plain_text(self, file_path: Path) -> ExtractionResult:
        for encoding in _TEXT_ENCODINGS:
            try:
                text = file_path.read_text(encoding=encoding)
                return ExtractionResult(text, "plain", "")
            except UnicodeDecodeError:
                continue
            except OSError as exc:
                return ExtractionResult("", "plain", str(exc))
        return ExtractionResult("", "plain", "No fue posible decodificar el archivo de texto")

    def _extract_pdf(self, file_path: Path) -> ExtractionResult:
        # Intento 1: PyMuPDF (mejor calidad, mantiene estructura de párrafos)
        if self._has_fitz:
            result = self._extract_pdf_fitz(file_path)
            if result.text.strip():
                return result

        # Intento 2: pdftotext CLI
        if self._pdftotext:
            result = self._extract_pdf_pdftotext(file_path)
            if result.text.strip():
                return result

        # Intento 3: regex básico sobre bytes (PDFs viejos sin estructura)
        result = self._extract_pdf_regex(file_path)
        if result.text.strip():
            return result

        # Intento 4: OCR (PDF escaneado como imagen)
        logger.info("PDF sin texto extraíble, intentando OCR: %s", file_path.name)
        return self.ocr_handler.extract_text(file_path)

    def _extract_pdf_fitz(self, file_path: Path) -> ExtractionResult:
        try:
            import fitz  # PyMuPDF
            pages: list[str] = []
            with fitz.open(str(file_path)) as doc:
                for page in doc:
                    text = page.get_text("text")
                    if text.strip():
                        pages.append(text)
            return ExtractionResult("\n\n".join(pages), "pdf_fitz", "")
        except Exception as exc:
            logger.warning("PyMuPDF falló en %s: %s", file_path.name, exc)
            return ExtractionResult("", "pdf_fitz", str(exc))

    def _extract_pdf_pdftotext(self, file_path: Path) -> ExtractionResult:
        try:
            result = subprocess.run(
                [self._pdftotext, "-layout", str(file_path), "-"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            text = result.stdout.strip()
            return ExtractionResult(text, "pdf_pdftotext", "")
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("pdftotext falló en %s: %s", file_path.name, exc)
            return ExtractionResult("", "pdf_pdftotext", str(exc))

    def _extract_pdf_regex(self, file_path: Path) -> ExtractionResult:
        try:
            raw = file_path.read_bytes().decode("latin-1", errors="ignore")
            matches = re.findall(r"\(([^()]{4,200})\)", raw)
            cleaned = " ".join(
                m for m in matches
                if "/" not in m and "\\" not in m and len(m.split()) > 1
            )
            return ExtractionResult(cleaned, "pdf_regex", "Extracción básica sin pdftotext")
        except OSError as exc:
            return ExtractionResult("", "pdf_regex", str(exc))

    def _extract_docx(self, file_path: Path) -> ExtractionResult:
        # Intento 1: python-docx (maneja tablas, cuadros de texto, headers)
        if self._has_docx:
            try:
                from docx import Document
                doc = Document(str(file_path))
                parts: list[str] = []

                # Párrafos del cuerpo
                for para in doc.paragraphs:
                    if para.text.strip():
                        parts.append(para.text)

                # Texto dentro de tablas
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            if cell.text.strip():
                                parts.append(cell.text)

                return ExtractionResult("\n".join(parts), "docx_python", "")
            except Exception as exc:
                logger.warning("python-docx falló en %s: %s", file_path.name, exc)

        # Fallback: XML manual (igual que el original)
        return self._extract_docx_xml(file_path)

    def _extract_docx_xml(self, file_path: Path) -> ExtractionResult:
        try:
            with ZipFile(file_path) as archive:
                xml_data = archive.read("word/document.xml")
        except OSError:
            return ExtractionResult("", "docx", "No fue posible abrir el DOCX")
        except KeyError:
            return ExtractionResult("", "docx", "El DOCX no contiene document.xml")

        root = ET.fromstring(xml_data)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs: list[str] = []
        for para in root.findall(".//w:p", ns):
            texts = [n.text for n in para.findall(".//w:t", ns) if n.text]
            if texts:
                paragraphs.append("".join(texts))
        return ExtractionResult("\n".join(paragraphs), "docx_xml", "")

    def _extract_pptx(self, file_path: Path) -> ExtractionResult:
        # Intento 1: python-pptx (extrae notas, cuadros de texto, SmartArt)
        if self._has_pptx:
            try:
                from pptx import Presentation
                prs = Presentation(str(file_path))
                slides: list[str] = []
                for slide in prs.slides:
                    slide_texts: list[str] = []
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for para in shape.text_frame.paragraphs:
                                text = para.text.strip()
                                if text:
                                    slide_texts.append(text)
                        # Notas del presentador
                    if slide.has_notes_slide:
                        notes_text = slide.notes_slide.notes_text_frame.text.strip()
                        if notes_text:
                            slide_texts.append(f"[Notas: {notes_text}]")
                    if slide_texts:
                        slides.append(" ".join(slide_texts))
                return ExtractionResult("\n".join(slides), "pptx_python", "")
            except Exception as exc:
                logger.warning("python-pptx falló en %s: %s", file_path.name, exc)

        # Fallback: XML manual (igual que el original)
        return self._extract_pptx_xml(file_path)

    def _extract_pptx_xml(self, file_path: Path) -> ExtractionResult:
        try:
            with ZipFile(file_path) as archive:
                slide_names = sorted(
                    n for n in archive.namelist()
                    if n.startswith("ppt/slides/slide") and n.endswith(".xml")
                )
                slides: list[str] = []
                for name in slide_names:
                    root = ET.fromstring(archive.read(name))
                    texts = [n.text for n in root.findall(".//{*}t") if n.text]
                    if texts:
                        slides.append(" ".join(texts))
        except OSError as exc:
            return ExtractionResult("", "pptx", str(exc))
        return ExtractionResult("\n".join(slides), "pptx_xml", "")

    def _extract_doc_fallback(self, file_path: Path) -> ExtractionResult:
        """Intenta extraer texto de archivos .doc (Word 97-2003) con antiword."""
        antiword = shutil.which("antiword")
        if antiword:
            try:
                result = subprocess.run(
                    [antiword, str(file_path)],
                    capture_output=True, text=True, timeout=15,
                )
                if result.stdout.strip():
                    return ExtractionResult(result.stdout, "doc_antiword", "")
            except (OSError, subprocess.SubprocessError):
                pass
        return ExtractionResult("", "doc", "Formato .doc requiere antiword instalado")

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------

    @staticmethod
    def _check_import(module: str) -> bool:
        """Verifica si un módulo está disponible sin importarlo."""
        import importlib.util
        return importlib.util.find_spec(module) is not None