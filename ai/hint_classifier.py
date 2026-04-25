"""Clasificación rápida por hints de portada."""

from __future__ import annotations

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

PORTADA_CHARS = 1500
MIN_HITS = 2

COURSE_CODES = {
    r"\b(IA|AI)\d+": "Inteligencia Artificial",
    r"\bBD\d+": "Base de Datos", 
    r"\bRD\d+": "Administracion de Redes",
    r"\bHE\d+": "Hacking Etico",
    r"\bTVirt\d+": "Tecnologias de Virtualizacion",
    r"\bTC\d+": "Tecnologias en la Nube",
    r"\bTI\d+": "Taller de Investigacion",
    r"\bDW\d+": "Desarrollo Web",
    r"\bDM\d+": "Desarrollo Movil",
}

# Unique keywords without overlap - EXTREME version
TITLE_KEYWORDS = {
    # Hacking - most specific
    "pentest": "Hacking Etico",
    "metasploit": "Hacking Etico",
    "exploit": "Hacking Etico",
    "nmap": "Hacking Etico",
    "cve": "Hacking Etico",
    "vulnerability": "Hacking Etico",
    "owasp": "Hacking Etico",
    "kali": "Hacking Etico",
    
    # Ciberseguridad
    "cibersecurity": "Ciberseguridad",
    "seguridad": "Ciberseguridad",
    "firewall": "Ciberseguridad",
    "criptografia": "Ciberseguridad",
    "oauth": "Ciberseguridad",
    
    # IA
    "tensorflow": "Inteligencia Artificial",
    "pytorch": "Inteligencia Artificial",
    "machine learning": "Inteligencia Artificial",
    "deep learning": "Inteligencia Artificial",
    "red neuronal": "Inteligencia Artificial",
    "neural": "Inteligencia Artificial",
    "gpt": "Inteligencia Artificial",
    
    # BD
    "mysql": "Base de Datos",
    "postgresql": "Base de Datos",
    "mongodb": "Base de Datos",
    "oracle": "Base de Datos",
    "sql": "Base de Datos",
    "database": "Base de Datos",
    
    # Virtualización
    "docker": "Tecnologias de Virtualizacion",
    "kubernetes": "Tecnologias de Virtualizacion",
    "vmware": "Tecnologias de Virtualizacion",
    "virtualbox": "Tecnologias de Virtualizacion",
    "hypervisor": "Tecnologias de Virtualizacion",
    
    # Nube
    "aws": "Tecnologias en la Nube",
    "azure": "Tecnologias en la Nube",
    "gcp": "Tecnologias en la Nube",
    "cloud": "Tecnologias en la Nube",
    "lambda": "Tecnologias en la Nube",
    "serverless": "Tecnologias en la Nube",
    
    # Redes
    "router": "Administracion de Redes",
    "switch": "Administracion de Redes",
    "tcp ip": "Administracion de Redes",
    "subnet": "Administracion de Redes",
    "vlan": "Administracion de Redes",
    "dns": "Administracion de Redes",
    "dhcp": "Administracion de Redes",
    "cisco": "Administracion de Redes",
    "network": "Administracion de Redes",
    "redes": "Administracion de Redes",
    
    # Web - full keywords to avoid conflicts
    "angular js": "Desarrollo Web",
    "react js": "Desarrollo Web",
    "vue js": "Desarrollo Web",
    "html css": "Desarrollo Web",
    "javascript": "Desarrollo Web",
    "node js": "Desarrollo Web",
    "rest api": "Desarrollo Web",
    "frontend": "Desarrollo Web",
    "backend": "Desarrollo Web",
    "fullstack": "Desarrollo Web",
    "bootstrap": "Desarrollo Web",
    
    # Móvil
    "android": "Desarrollo Movil",
    "ios": "Desarrollo Movil",
    "kotlin": "Desarrollo Movil",
    "flutter": "Desarrollo Movil",
    "swift": "Desarrollo Movil",
    "react native": "Desarrollo Movil",
    
    # Software
    "scrum": "Desarrollo de Software",
    "agile": "Desarrollo de Software",
    "uml": "Desarrollo de Software",
    "testing": "Desarrollo de Software",
    "git": "Desarrollo de Software",
    
    # Datos
    "pandas": "Ciencia de Datos",
    "big data": "Ciencia de Datos",
    "hadoop": "Ciencia de Datos",
    "spark": "Ciencia de Datos",
    "tableau": "Ciencia de Datos",
    
    # SO
    "kernel": "Sistemas Operativos",
    "linux": "Sistemas Operativos",
    "ubuntu": "Sistemas Operativos",
    "windows server": "Sistemas Operativos",
    "bash": "Sistemas Operativos",
    "shell": "Sistemas Operativos",
    
    # Arquitectura
    "cpu": "Arquitectura de Computadoras",
    "gpu": "Arquitectura de Computadoras",
    "assembly": "Arquitectura de Computadoras",
    "register": "Arquitectura de Computadoras",
    
    # Investigación
    "tesis": "Taller de Investigacion",
    "investigacion": "Taller de Investigacion",
    "metodologia": "Taller de Investigacion",
    "hipotesis": "Taller de Investigacion",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify_by_hints(text: str, hints: dict[str, set[str]], *, portada_chars: int = PORTADA_CHARS, multi_category: bool = False):
    """Multi-category classification for documents with multiple topics.
    
    Args:
        text: Document text
        hints: Category keywords dictionary
        portada_chars: Characters to analyze from start
        multi_category: If True, return list of categories with scores
    
    Returns:
        Tuple of (primary_category, confidence) or list of (category, score) if multi_category=True
    """
    if not text or not hints:
        return (None, 0.0) if not multi_category else []

    normalized = _normalize(text[:portada_chars])
    words = set(normalized.split())
    raw = text[:portada_chars].lower()

    # Priority 1: Course codes (highest priority)
    for pattern, category in COURSE_CODES.items():
        if re.search(pattern, raw, re.IGNORECASE):
            if multi_category:
                return [(category, 0.95)]
            return category, 0.95

    # Priority 2: Exact title keywords
    category_scores = {}
    for keyword, category in TITLE_KEYWORDS.items():
        if keyword in raw:
            # Exact match = high score
            category_scores[category] = category_scores.get(category, 0.0) + 2.0

    # Priority 3: Count hits from category hints (lower weight)
    for category, keywords in hints.items():
        hits = sum(1 for kw in keywords if kw in words)
        if hits >= 1:
            current = category_scores.get(category, 0.0)
            category_scores[category] = current + (hits * 0.5)

    if not category_scores:
        return (None, 0.0) if not multi_category else []

    # Sort by score
    sorted_scores = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    
    if multi_category:
        # Return top categories that meet threshold
        result = [(cat, min(0.95, 0.40 + score * 0.15)) for cat, score in sorted_scores if score >= 1.0]
        return result[:3]  # Top 3 categories
    
    # Single category mode
    best_category, best_score = sorted_scores[0]
    
    # Require significant lead over second place
    if len(sorted_scores) >= 2:
        second_score = sorted_scores[1][1]
        if best_score == second_score:
            return None, 0.0  # Tie
    
    confidence = min(0.90, 0.45 + best_score * 0.12)
    return best_category, confidence


def get_multi_categories(text: str, hints: dict[str, set[str]], *, portada_chars: int = PORTADA_CHARS) -> list[tuple[str, float]]:
    """Get all categories that match a document with scores.
    
    Returns list of (category, confidence) sorted by relevance.
    """
    result = classify_by_hints(text, hints, portada_chars=portada_chars, multi_category=True)
    return result if result else []