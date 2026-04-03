"""Clasificación rápida por hints de portada.

Estrategia:
  1. Tomar las primeras N caracteres del documento (portada).
  2. Buscar coincidencias con KNOWN_CATEGORY_HINTS.
  3. Si hay suficientes hits → clasificar directamente con confianza alta.
  4. Si no → devolver None para que el clasificador por embedding tome el control.

Ventajas sobre embedding puro:
  - Funciona perfecto con nombres de docentes y términos técnicos específicos.
  - Confianza determinista — si dice "aurora moreno" es Redes, punto.
  - Muy rápido — sin cómputo vectorial.
"""

from __future__ import annotations

import logging
import unicodedata
import re

logger = logging.getLogger(__name__)

# Cuántos caracteres de la portada analizar (las primeras ~2 páginas)
PORTADA_CHARS = 1200

# Mínimo de hits para clasificar con confianza alta
MIN_HITS_HIGH_CONFIDENCE = 2   # 2+ coincidencias → confianza 0.95
MIN_HITS_LOW_CONFIDENCE  = 1   # 1 coincidencia  → confianza 0.72


def classify_by_hints(
    text: str,
    hints: dict[str, set[str]],
    *,
    portada_chars: int = PORTADA_CHARS,
) -> tuple[str | None, float]:
    """Clasifica un documento buscando hints en su portada.

    Args:
        text: Texto completo del documento (se analiza solo el inicio).
        hints: Diccionario {categoria: set_de_palabras_clave}.
        portada_chars: Cuántos caracteres iniciales considerar como portada.

    Returns:
        Tupla (categoria, confianza). None si no hay suficientes hits.
    """
    if not text or not hints:
        return None, 0.0

    # Analizar portada + un poco más para capturar encabezados de secciones
    portada = _normalize(text[:portada_chars])
    portada_words = set(portada.split())

    scores: list[tuple[int, str]] = []

    for category, keywords in hints.items():
        # Normalizar hints igual que el texto
        normalized_hints = {_normalize(kw) for kw in keywords}

        # Contar hits: palabra exacta O como substring (para nombres compuestos)
        hits = 0
        for hint in normalized_hints:
            # Match exacto por palabra
            if hint in portada_words:
                hits += 1
            # Match como frase (para hints de 2+ palabras como "machine learning")
            elif " " in hint and hint in portada:
                hits += 1

        if hits > 0:
            scores.append((hits, category))

    if not scores:
        return None, 0.0

    scores.sort(reverse=True)
    best_hits, best_category = scores[0]

    # Verificar que haya un ganador claro (evitar empates)
    if len(scores) >= 2:
        second_hits = scores[1][0]
        # Si hay empate exacto, no clasificar con hints (dejar al embedding)
        if best_hits == second_hits:
            logger.debug(
                "Empate en hints (%d hits): %s vs %s — delegando a embedding",
                best_hits, best_category, scores[1][1],
            )
            return None, 0.0

    if best_hits >= MIN_HITS_HIGH_CONFIDENCE:
        confidence = min(0.95, 0.75 + best_hits * 0.05)
        logger.info(
            "Clasificado por hints: '%s' (%d hits, confianza=%.2f)",
            best_category, best_hits, confidence,
        )
        return best_category, confidence

    if best_hits >= MIN_HITS_LOW_CONFIDENCE:
        logger.debug(
            "Hit único en hints: '%s' (%d hit, confianza=0.72)",
            best_category, best_hits,
        )
        return best_category, 0.72

    return None, 0.0


def extract_portada_text(text: str, chars: int = PORTADA_CHARS) -> str:
    """Extrae y normaliza el texto de portada de un documento."""
    return _normalize(text[:chars])


def _normalize(text: str) -> str:
    """Normaliza texto para comparación: minúsculas, sin acentos, sin puntuación."""
    # Eliminar acentos
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    # Minúsculas
    text = text.lower()
    # Eliminar caracteres no alfanuméricos excepto espacios
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Colapsar espacios
    text = re.sub(r"\s+", " ", text).strip()
    return text