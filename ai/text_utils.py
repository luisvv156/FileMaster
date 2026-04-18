"""Utilidades de normalización, limpieza y tokenización de texto para FileMaster."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import TypeAlias

Tokens: TypeAlias = list[str]

# Increased for better semantic analysis
MAX_TEXT_LENGTH = 12000
PORTADA_BOOST_CHARS = 1500
PORTADA_BOOST_REPEATS = 3

# ── Stopwords ──────────────────────────────────────────────────────────────────
# FIX: eliminados términos académicos que SÍ son relevantes para clasificar:
# "practica", "reporte", "informe", "proyecto", "unidad", "tema", etc.
# Esos aparecen en portadas y ayudan a identificar el tipo de documento.
STOPWORDS: frozenset[str] = frozenset({
    # Español — artículos, preposiciones, pronombres, verbos auxiliares
    "a", "al", "algo", "ambos", "ante", "antes", "aquel", "aqui",
    "como", "con", "cual", "de", "del", "desde", "donde",
    "el", "ella", "ellas", "ellos", "en", "entre", "era", "eres",
    "es", "esa", "ese", "eso", "esta", "este", "esto", "fue",
    "ha", "hay", "la", "las", "le", "lo", "los", "mas", "mi",
    "muy", "ni", "no", "nos", "o", "para", "pero", "por",
    "que", "quien", "se", "si", "sin", "sobre", "son", "su", "sus",
    "tambien", "tan", "te", "tiene", "todo", "tu",
    "un", "una", "uno", "unos", "usted", "y", "ya", "yo",
    # Inglés — básico
    "an", "and", "are", "as", "at", "be", "been", "by",
    "for", "from", "has", "have", "in", "is", "it", "its",
    "not", "of", "on", "or", "that", "the", "their", "this",
    "to", "was", "were", "which", "with",
    # Extensiones de archivo
    "pdf", "docx", "doc", "pptx", "ppt", "txt", "xlsx", "xls",
    "jpg", "jpeg", "png", "csv",
    # Términos genéricos SIN valor clasificatorio
    "documento", "archivo", "file", "version", "final", "nuevo",
    "copia", "copy", "borrador", "draft", "revision", "rev",
    "untitled", "sin", "titulo", "nombre",
})
# NOTA: Se eliminaron intencionalmente de stopwords:
# practica, reporte, informe, proyecto, tarea, actividad, trabajo,
# unidad, capitulo, tema, introduccion, clase, ejercicio, entrega, parcial
# → Estas palabras SÍ ayudan a clasificar documentos académicos.

# ── Sufijos para lematización ligera ──────────────────────────────────────────
_SUFFIXES_ES = (
    "aciones", "acion", "amiento", "idades", "idad",
    "mente", "ando", "iendo", "ados", "idos", "ado", "ido",
    "ares", "eres", "ires", "ar", "er", "ir",
    "mos", "ais", "an", "en",
)


# ── Funciones públicas ────────────────────────────────────────────────────────

def clean_text(text: str, *, max_length: int = MAX_TEXT_LENGTH) -> str:
    """Limpia y normaliza texto para embeddings.

    FIX: límite subido a 8000 chars para capturar portadas completas.
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+\.\S+", " ", text)
    text = re.sub(r"\b\d+\b", " ", text)
    text = re.sub(r"[^a-z0-9áéíóúüñ\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_length]


def boost_portada(text: str, boost_chars: int = None) -> str:
    """Amplifica las primeras líneas del documento para mejor análisis semántico.

    La portada académica contiene información clave: materia, docente, institución.
    Repetirla múltiples veces aumenta su peso en el embedding sin perder contexto.

    Args:
        text: Texto completo ya limpio.
        boost_chars: Caracteres de portada a amplify (None usa global).

    Returns:
        Texto con portada amplificada + contenido completo.
    """
    boost = boost_chars or PORTADA_BOOST_CHARS
    repeats = PORTADA_BOOST_REPEATS
    
    if not text or len(text) < 100:
        return text
    
    # Extraer portada (inicio del documento)
    portada = text[:boost].strip()
    if not portada:
        return text
    
    # Amplificar portada + mantener resto completo
    boosted = " ".join([portada] * repeats)
    return f"{boosted} {text}"


def normalize_text(text: str) -> str:
    return clean_text(text, max_length=len(text) + 1)


def tokenize(text: str, *, min_length: int = 3, lemmatize: bool = True) -> Tokens:
    cleaned = clean_text(text)
    raw_tokens = cleaned.split()

    tokens: Tokens = []
    for token in raw_tokens:
        if len(token) < min_length:
            continue
        if token in STOPWORDS:
            continue
        if not any(ch in "aeiouáéíóúü" for ch in token):
            continue
        if _is_garbage_token(token):
            continue
        if lemmatize:
            token = _lemmatize_es(token)
        if len(token) >= min_length and token not in STOPWORDS:
            tokens.append(token)
    return tokens


def token_frequencies(text: str, *, min_length: int = 3) -> Counter[str]:
    return Counter(tokenize(text, min_length=min_length))


def title_from_keywords(keywords: list[str], fallback: str = "Documento") -> str:
    clean = [kw.strip().title() for kw in keywords if kw.strip() and len(kw.strip()) > 2]
    return " ".join(clean[:3]) if clean else fallback


def detect_language(text: str) -> str:
    es_markers = {"de", "la", "el", "en", "que", "y", "con", "para", "una", "los"}
    en_markers = {"the", "of", "and", "in", "to", "a", "is", "that", "it", "for"}
    words = set(text.lower().split())
    es_score = len(words & es_markers)
    en_score = len(words & en_markers)
    return "es" if es_score >= en_score else "en"


def truncate_for_embedding(text: str, max_chars: int = MAX_TEXT_LENGTH) -> str:
    """Trunca respetando el límite de Sentence-BERT (~512 tokens ≈ 8000 chars)."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    return truncated[:last_space] if last_space > max_chars // 2 else truncated


def generate_category_name(keywords: list[str]) -> str:
    """Genera un nombre de categoría descriptivo desde keywords."""
    if not keywords:
        return "Archivos Varios"
    
    # Mapeo de keywords a categorías (ordenados por especificidad)
    category_mapping = {
        # IA y Machine Learning
        "machine learning": "Inteligencia Artificial",
        "deep learning": "Inteligencia Artificial",
        "neural network": "Inteligencia Artificial",
        "red neuronal": "Inteligencia Artificial",
        "tensorflow": "Inteligencia Artificial",
        "pytorch": "Inteligencia Artificial",
        "gpt": "Inteligencia Artificial",
        "llm": "Inteligencia Artificial",
        "transformer": "Inteligencia Artificial",
        "nlp": "Inteligencia Artificial",
        "computer vision": "Inteligencia Artificial",
        "yolo": "Inteligencia Artificial",
        
        # Base de Datos
        "sql": "Base de Datos",
        "mysql": "Base de Datos",
        "postgresql": "Base de Datos",
        "oracle": "Base de Datos",
        "mongodb": "Base de Datos",
        "database": "Base de Datos",
        "relacional": "Base de Datos",
        "sqlite": "Base de Datos",
        "nosql": "Base de Datos",
        
        # Redes (solo si no hay web-related)
        "redes": "Administracion de Redes",
        "router": "Administracion de Redes",
        "tcp": "Administracion de Redes",
        "ip": "Administracion de Redes",
        "subnet": "Administracion de Redes",
        "vlan": "Administracion de Redes",
        "dns": "Administracion de Redes",
        "dhcp": "Administracion de Redes",
        
        # Hacking
        "pentest": "Hacking Etico",
        "exploit": "Hacking Etico",
        "metasploit": "Hacking Etico",
        "nmap": "Hacking Etico",
        "payload": "Hacking Etico",
        
        # Ciberseguridad
        "security": "Ciberseguridad",
        "cibersecurity": "Ciberseguridad",
        "criptografia": "Ciberseguridad",
        "encryption": "Ciberseguridad",
        
        # Virtualización
        "virtual": "Tecnologias de Virtualizacion",
        "docker": "Tecnologias de Virtualizacion",
        "kubernetes": "Tecnologias de Virtualizacion",
        "vmware": "Tecnologias de Virtualizacion",
        
        # Nube
        "cloud": "Tecnologias en la Nube",
        "aws": "Tecnologias en la Nube",
        "azure": "Tecnologias en la Nube",
        "gcp": "Tecnologias en la Nube",
        
        # Investigación
        "investigacion": "Taller de Investigacion",
        "tesis": "Taller de Investigacion",
        "methodology": "Taller de Investigacion",
        "metodologia": "Taller de Investigacion",
        
        # Desarrollo Web
        "html": "Desarrollo Web",
        "css": "Desarrollo Web",
        "javascript": "Desarrollo Web",
        "react": "Desarrollo Web",
        "angular": "Desarrollo Web",
        "vue": "Desarrollo Web",
        
        # Desarrollo Móvil
        "android": "Desarrollo Movil",
        "ios": "Desarrollo Movil",
        "flutter": "Desarrollo Movil",
        "kotlin": "Desarrollo Movil",
        "swift": "Desarrollo Movil",
        
        # Desarrollo de Software
        "scrum": "Desarrollo de Software",
        "agile": "Desarrollo de Software",
        "uml": "Desarrollo de Software",
        "testing": "Desarrollo de Software",
        "refactoring": "Desarrollo de Software",
        
        # Ciencia de Datos
        "data": "Ciencia de Datos",
        "analytics": "Ciencia de Datos",
        "pandas": "Ciencia de Datos",
        "big data": "Ciencia de Datos",
        "visualization": "Ciencia de Datos",
        
        # Matemáticas/discretas
        "graph": "Matematicas Discretas",
        "grafo": "Matematicas Discretas",
        "discrete": "Matematicas Discretas",
        
        # Arquitectura
        "cpu": "Arquitectura de Computadoras",
        "gpu": "Arquitectura de Computadoras",
        "assembly": "Arquitectura de Computadoras",
        "kernel": "Sistemas Operativos",
        
        # Estadística
        "statistics": "Estadistica",
        "mean": "Estadistica",
        "variance": "Estadistica",
    }
    
    keywords_text = " ".join(keywords).lower()
    
    # Buscar coincidencias exactas primero
    for key, category in category_mapping.items():
        if key in keywords_text:
            return category
    
    # Si no hay coincidencia, usar el primer keyword válido
    if keywords:
        return keywords[0].title()
    
    return "Archivos Varios"


# ── Helpers internos ──────────────────────────────────────────────────────────

def _lemmatize_es(word: str) -> str:
    if len(word) <= 5:
        return word
    for suffix in _SUFFIXES_ES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _is_garbage_token(word: str) -> bool:
    vowels = set("aeiouáéíóúü")
    vowel_count = sum(1 for ch in word if ch in vowels)
    if len(word) >= 5 and vowel_count / len(word) < 0.20:
        return True
    consonant_streak = 0
    for ch in word:
        if ch.isalpha() and ch not in vowels:
            consonant_streak += 1
            if consonant_streak > 4:
                return True
        else:
            consonant_streak = 0
    return False