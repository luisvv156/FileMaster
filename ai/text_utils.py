"""Utilidades de normalizacion y tokenizacion."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter


STOPWORDS = {
    "a",
    "al",
    "algo",
    "ante",
    "como",
    "con",
    "de",
    "del",
    "desde",
    "docx",
    "documento",
    "dos",
    "el",
    "ella",
    "en",
    "entre",
    "era",
    "es",
    "esa",
    "ese",
    "esta",
    "este",
    "esto",
    "for",
    "ha",
    "hay",
    "ia",
    "la",
    "las",
    "lo",
    "los",
    "mas",
    "mi",
    "muy",
    "no",
    "pdf",
    "por",
    "pptx",
    "que",
    "se",
    "sin",
    "sobre",
    "su",
    "sus",
    "tema",
    "the",
    "to",
    "txt",
    "un",
    "una",
    "uno",
    "y",
}


def normalize_text(text: str) -> str:
    text = text or ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"[^a-z0-9áéíóúüñ]+", " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str, *, min_length: int = 3) -> list[str]:
    normalized = normalize_text(text)
    tokens = []
    for token in normalized.split():
        if len(token) < min_length:
            continue
        if token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def token_frequencies(text: str, *, min_length: int = 3) -> Counter[str]:
    return Counter(tokenize(text, min_length=min_length))


def title_from_keywords(keywords: list[str], fallback: str = "Documentos") -> str:
    clean = [keyword.strip().title() for keyword in keywords if keyword.strip()]
    if not clean:
        return fallback
    return " ".join(clean[:2])
