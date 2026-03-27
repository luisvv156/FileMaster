"""Extraccion de palabras clave."""

from __future__ import annotations

from ai.text_utils import token_frequencies


class KeywordExtractor:
    def extract(self, text: str, limit: int = 5) -> list[str]:
        frequencies = token_frequencies(text)
        return [token for token, _count in frequencies.most_common(limit)]
