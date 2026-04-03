"""Renombrado inteligente de documentos basado en categoría y palabras clave."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_MAX_NAME_LENGTH = 60


class SmartRenamer:
    """Genera nombres descriptivos para documentos a partir de su metadata.

    Formato de salida:
        {categoria}_{keyword1}_{keyword2}{extension}

    Ejemplo:
        hacking_etico_vulnerabilidad_exploit.pdf
    """

    # ✅ suggest_name DENTRO de la clase (indentado con 4 espacios)
    def suggest_name(
        self,
        file_path: Path,
        category: str,
        keywords: list[str] | None = None,
    ) -> str:
        keywords = keywords or []

        try:
            category_slug = self._slugify(category) or "documento"

            kw_slugs = [
                s for kw in keywords
                if (s := self._slugify(kw))
            ][:2]

            extension = file_path.suffix.lower() or ".bin"

            parts = [category_slug] + kw_slugs
            base = "_".join(part for part in parts if part)

            if len(base) > _MAX_NAME_LENGTH:
                base = base[:_MAX_NAME_LENGTH].rstrip("_")

            result = f"{base}{extension}"
            logger.debug("Nombre sugerido: %s → %s", file_path.name, result)
            return result

        except Exception as exc:
            logger.warning(
                "Error generando nombre para '%s': %s. Usando nombre original.",
                file_path.name, exc,
            )
            return file_path.name

    def suggest_name_from_record(self, record: "FileRecord") -> str:  # type: ignore[name-defined]
        """Atajo que opera directamente sobre un FileRecord."""
        return self.suggest_name(
            file_path=Path(record.path),
            category=record.category or "documento",
            keywords=record.keywords or [],
        )

    @staticmethod
    def _slugify(value: str) -> str:
        """Convierte un texto en slug seguro para nombre de archivo."""
        if not value:
            return ""
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = value.strip("_")
        return value[:20]


# ✅ Función libre — FUERA de la clase (sin indentación)
def generate_name(keywords: list[str], category: str, extension: str = ".pdf") -> str:
    """Función libre para usar directamente desde controller.py."""
    renamer = SmartRenamer()
    dummy_path = Path(f"documento{extension}")
    return renamer.suggest_name(dummy_path, category, keywords)