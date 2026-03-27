"""Extraccion de texto para los formatos soportados."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from config.settings import IMAGE_EXTENSIONS
from core.models import ExtractionResult
from core.ocr_handler import OCRHandler


class TextExtractor:
    def __init__(self) -> None:
        self.ocr_handler = OCRHandler()
        self._pdftotext = shutil.which("pdftotext")

    def extract(self, file_path: Path) -> ExtractionResult:
        suffix = file_path.suffix.lower()
        if suffix in {".txt", ".md", ".csv", ".json", ".log", ".py"}:
            return self._extract_plain_text(file_path)
        if suffix == ".docx":
            return self._extract_docx(file_path)
        if suffix == ".pptx":
            return self._extract_pptx(file_path)
        if suffix == ".pdf":
            return self._extract_pdf(file_path)
        if suffix in IMAGE_EXTENSIONS:
            return self.ocr_handler.extract_text(file_path)
        return ExtractionResult("", "unsupported", f"Formato no soportado: {suffix}")

    def _extract_plain_text(self, file_path: Path) -> ExtractionResult:
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                return ExtractionResult(file_path.read_text(encoding=encoding), "plain", "")
            except UnicodeDecodeError:
                continue
            except OSError:
                break
        return ExtractionResult("", "plain", "No fue posible leer el archivo")

    def _extract_docx(self, file_path: Path) -> ExtractionResult:
        try:
            with ZipFile(file_path) as archive:
                xml_data = archive.read("word/document.xml")
        except OSError:
            return ExtractionResult("", "docx", "No fue posible abrir el archivo DOCX")
        except KeyError:
            return ExtractionResult("", "docx", "El DOCX no contiene document.xml")

        root = ET.fromstring(xml_data)
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for paragraph in root.findall(".//w:p", namespace):
            texts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
            if texts:
                paragraphs.append("".join(texts))
        return ExtractionResult("\n".join(paragraphs), "docx", "")

    def _extract_pptx(self, file_path: Path) -> ExtractionResult:
        try:
            with ZipFile(file_path) as archive:
                slide_names = sorted(name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))
                slides = []
                for slide_name in slide_names:
                    root = ET.fromstring(archive.read(slide_name))
                    texts = [node.text for node in root.findall(".//{*}t") if node.text]
                    if texts:
                        slides.append(" ".join(texts))
        except OSError:
            return ExtractionResult("", "pptx", "No fue posible abrir el archivo PPTX")

        return ExtractionResult("\n".join(slides), "pptx", "")

    def _extract_pdf(self, file_path: Path) -> ExtractionResult:
        if self._pdftotext:
            try:
                result = subprocess.run(
                    [self._pdftotext, str(file_path), "-"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                text = result.stdout.strip()
                if text:
                    return ExtractionResult(text, "pdf", "")
            except (OSError, subprocess.SubprocessError):
                pass

        try:
            raw = file_path.read_bytes().decode("latin-1", errors="ignore")
        except OSError:
            return ExtractionResult("", "pdf", "No fue posible leer el PDF")

        matches = re.findall(r"\(([^()]{4,})\)", raw)
        cleaned = " ".join(match for match in matches if "/" not in match and "\\" not in match)
        if cleaned.strip():
            return ExtractionResult(cleaned, "pdf", "Extraccion basica sin pdftotext")
        return ExtractionResult("", "pdf", "No se encontro texto extraible en el PDF")
