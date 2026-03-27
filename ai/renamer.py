"""Renombrado inteligente basado en categoria y palabras clave."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


class SmartRenamer:
    def suggest_name(self, file_path: Path, category: str, keywords: list[str] | None = None) -> str:
        keywords = keywords or []
        category_slug = self._slugify(category) or "documento"
        keyword_part = "_".join(self._slugify(keyword) for keyword in keywords[:2] if self._slugify(keyword))
        date_part = datetime.now().date().isoformat()
        base = "_".join(part for part in [category_slug, keyword_part, date_part] if part)
        return f"{base}{file_path.suffix.lower()}"

    def _slugify(self, value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        return value.strip("_")
