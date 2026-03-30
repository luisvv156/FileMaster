"""Utilidades de normalización, limpieza y tokenización de texto para FileMaster."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import TypeAlias

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------
Tokens: TypeAlias = list[str]

# ---------------------------------------------------------------------------
# Límite de caracteres para no saturar Sentence-BERT (512 tokens ≈ ~2000 chars)
# ---------------------------------------------------------------------------
MAX_TEXT_LENGTH = 2000

# ---------------------------------------------------------------------------
# Stopwords combinadas: español + inglés + términos académicos/técnicos
# ---------------------------------------------------------------------------
STOPWORDS: frozenset[str] = frozenset({
    # Español — artículos, preposiciones, pronombres
    "a", "al", "algo", "ambos", "ante", "antes", "aquel", "aqui",
    "como", "con", "cual", "de", "del", "desde", "donde",
    "el", "ella", "ellas", "ellos", "en", "entre", "era", "eres",
    "es", "esa", "ese", "eso", "esta", "este", "esto", "fue",
    "ha", "hay", "la", "las", "le", "lo", "los", "mas", "mi",
    "muy", "ni", "no", "nos", "o", "para", "pero", "por",
    "que", "quien", "se", "si", "sin", "sobre", "son", "su", "sus",
    "tambien", "tan", "te", "tema", "tiene", "todo", "tu",
    "un", "una", "uno", "unos", "usted", "y", "ya", "yo",
    # Inglés — básico
    "a", "an", "and", "are", "as", "at", "be", "been", "by",
    "for", "from", "has", "have", "in", "is", "it", "its",
    "not", "of", "on", "or", "that", "the", "their", "this",
    "to", "was", "were", "which", "with",
    # Extensiones de archivo (aparecen en nombres)
    "pdf", "docx", "doc", "pptx", "ppt", "txt", "xlsx", "xls",
    "jpg", "jpeg", "png", "csv",
    # Términos genéricos académicos/documentales
    "documento", "archivo", "file", "version", "final", "nuevo",
    "copia", "copy", "borrador", "draft", "revision", "rev",
    "untitled", "sin", "titulo", "nombre",
})

# ---------------------------------------------------------------------------
# Sufijos comunes para lematización ligera en español (sin dependencia externa)
# ---------------------------------------------------------------------------
_SUFFIXES_ES = (
    "aciones", "acion", "amiento", "amiento", "idades", "idad",
    "mente", "ando", "iendo", "ados", "idos", "ado", "ido",
    "ares", "eres", "ires", "ar", "er", "ir",
    "mos", "ais", "an", "en",
)


# ---------------------------------------------------------------------------
# Funciones públicas
# ---------------------------------------------------------------------------

def clean_text(text: str, *, max_length: int = MAX_TEXT_LENGTH) -> str:
    """Limpia y normaliza texto para su uso en el pipeline NLP/embeddings.

    Pasos:
    1. Normalización Unicode NFKD (elimina acentos diacríticos)
    2. Conversión a minúsculas
    3. Eliminación de URLs, emails y caracteres especiales
    4. Colapso de espacios múltiples
    5. Truncado a `max_length` caracteres para respetar límite de Sentence-BERT

    Args:
        text: Texto crudo extraído del documento.
        max_length: Límite de caracteres (default 2000).

    Returns:
        Texto limpio listo para embeddings o tokenización.
    """
    if not text:
        return ""

    # Normalización Unicode → eliminar diacríticos combinados
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))

    # Minúsculas
    text = text.lower()

    # Eliminar URLs y emails
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+\.\S+", " ", text)

    # Eliminar números puros (conservar alfanuméricos como "ipv4", "cap3")
    text = re.sub(r"\b\d+\b", " ", text)

    # Eliminar caracteres no alfanuméricos (conservar letras españolas)
    text = re.sub(r"[^a-z0-9áéíóúüñ\s]", " ", text)

    # Colapsar espacios
    text = re.sub(r"\s+", " ", text).strip()

    # Truncar para no exceder límite del modelo de embeddings
    return text[:max_length]


def normalize_text(text: str) -> str:
    """Normalización básica sin truncado. Mantiene compatibilidad con el stub."""
    return clean_text(text, max_length=len(text) + 1)


def tokenize(text: str, *, min_length: int = 3, lemmatize: bool = True) -> Tokens:
    """Tokeniza texto limpio y filtra stopwords.

    Args:
        text: Texto ya normalizado (idealmente pasado por `clean_text`).
        min_length: Longitud mínima de token (default 3).
        lemmatize: Si True, aplica lematización ligera en español.

    Returns:
        Lista de tokens filtrados.
    """
    cleaned = clean_text(text)
    raw_tokens = cleaned.split()

    tokens: Tokens = []
    for token in raw_tokens:
        if len(token) < min_length:
            continue
        if token in STOPWORDS:
            continue
        if lemmatize:
            token = _lemmatize_es(token)
        if len(token) >= min_length and token not in STOPWORDS:
            tokens.append(token)
    return tokens


def token_frequencies(text: str, *, min_length: int = 3) -> Counter[str]:
    """Retorna un Counter con la frecuencia de cada token en el texto."""
    return Counter(tokenize(text, min_length=min_length))


def title_from_keywords(keywords: list[str], fallback: str = "Documento") -> str:
    """Genera un título legible a partir de las keywords más relevantes.

    Toma máximo 3 keywords, las capitaliza y las une. Si no hay keywords,
    retorna el fallback.

    Args:
        keywords: Lista de keywords ordenadas por relevancia (mayor primero).
        fallback: Texto a retornar si no hay keywords válidas.

    Returns:
        Título formado por las primeras keywords.
    """
    clean = [kw.strip().title() for kw in keywords if kw.strip() and len(kw.strip()) > 2]
    return " ".join(clean[:3]) if clean else fallback


def detect_language(text: str) -> str:
    """Detecta heurísticamente si el texto es español o inglés.

    Cuenta palabras clave características de cada idioma. No depende de
    bibliotecas externas para mantener el agente 100% offline.

    Returns:
        "es" o "en"
    """
    es_markers = {"de", "la", "el", "en", "que", "y", "con", "para", "una", "los"}
    en_markers = {"the", "of", "and", "in", "to", "a", "is", "that", "it", "for"}

    words = set(text.lower().split())
    es_score = len(words & es_markers)
    en_score = len(words & en_markers)
    return "es" if es_score >= en_score else "en"


def truncate_for_embedding(text: str, max_chars: int = MAX_TEXT_LENGTH) -> str:
    """Trunca el texto al límite seguro para Sentence-BERT.

    Sentence-BERT procesa máximo 512 tokens wordpiece. ~2000 caracteres es
    un límite conservador que evita truncados silenciosos del modelo.

    Args:
        text: Texto limpio.
        max_chars: Límite de caracteres.

    Returns:
        Texto truncado.
    """
    if len(text) <= max_chars:
        return text
    # Truncar en el último espacio para no cortar palabras
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    return truncated[:last_space] if last_space > max_chars // 2 else truncated


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _lemmatize_es(word: str) -> str:
    """Lematización ligera en español por truncado de sufijos conocidos.

    No usa spaCy ni NLTK. Es una aproximación rápida y sin dependencias.
    Suficiente para mejorar clustering; el keyword_extractor usará spaCy.

    Args:
        word: Token en minúsculas ya normalizado.

    Returns:
        Raíz aproximada del token.
    """
    if len(word) <= 5:
        return word
    for suffix in _SUFFIXES_ES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word