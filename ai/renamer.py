"""Renombrado inteligente de documentos basado en categoría y palabras clave."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Longitud máxima del nombre base (sin extensión)
_MAX_NAME_LENGTH = 60


class SmartRenamer:
    """Genera nombres descriptivos para documentos a partir de su metadata.

    Formato de salida:
        {categoria}_{keyword1}_{keyword2}_{fecha}{extension}

    Ejemplo:
        redes_protocolo_tcp_2026-03-29.pdf
    """

    def suggest_name(
        self,
        file_path: Path,
        category: str,
        keywords: list[str] | None = None,
    ) -> str:
        """Genera un nombre de archivo sugerido.

        Args:
            file_path: Ruta original del archivo (para obtener la extensión).
            category: Categoría temática del documento (e.g. "Redes").
            keywords: Lista de keywords ordenadas por relevancia (mayor primero).

        Returns:
            Nombre de archivo con extensión. Si la generación falla,
            retorna el nombre original limpio.
        """
        keywords = keywords or []

        try:
            category_slug = self._slugify(category) or "documento"

            # Tomar hasta 3 keywords con slug válido
            kw_slugs = [
                s for kw in keywords
                if (s := self._slugify(kw))
            ][:3]

            date_part = datetime.now().date().isoformat()
            extension = file_path.suffix.lower() or ".bin"

            parts = [category_slug] + kw_slugs + [date_part]
            base = "_".join(part for part in parts if part)

            # Truncar si el nombre es demasiado largo
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
        """Atajo que opera directamente sobre un FileRecord.

        Args:
            record: FileRecord con `path`, `category` y `keywords` ya poblados.

        Returns:
            Nombre de archivo sugerido.
        """
        return self.suggest_name(
            file_path=Path(record.path),
            category=record.category or "documento",
            keywords=record.keywords or [],
        )

    @staticmethod
    def _slugify(value: str) -> str:
        """Convierte un texto en un slug seguro para nombre de archivo.

        - Minúsculas
        - Solo letras, dígitos y guiones bajos
        - Sin guiones bajos al inicio o al final
        - Máximo 20 caracteres por slug individual
        """
        if not value:
            return ""
        value = value.strip().lower()
        # Reemplazar caracteres no válidos por guión bajo
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = value.strip("_")
        return value[:20]


def generate_name(keywords: list[str], category: str, extension: str = ".pdf") -> str:
    """Función libre que usa el controller.py directamente.

    Args:
        keywords: Keywords del documento ordenadas por relevancia.
        category: Categoría temática asignada.
        extension: Extensión del archivo (con punto, e.g. ".pdf").

    Returns:
        Nombre de archivo sugerido.
    """
    renamer = SmartRenamer()
    dummy_path = Path(f"documento{extension}")
    return renamer.suggest_name(dummy_path, category, keywords)