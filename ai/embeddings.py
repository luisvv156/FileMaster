"""Embeddings semánticos locales con Sentence-BERT (all-MiniLM-L6-v2).

El modelo se descarga automáticamente en la primera ejecución (~90 MB)
y queda en caché local. A partir de ahí, opera 100% offline.
"""

from __future__ import annotations

import logging
import math
from functools import lru_cache
from typing import TYPE_CHECKING

from ai.text_utils import clean_text, truncate_for_embedding

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer as _ST

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_SIZE = 384          # Dimensión fija del modelo elegido
BATCH_SIZE = 32            # Documentos por lote al encodear en masa


# ---------------------------------------------------------------------------
# Carga lazy del modelo (singleton)
# ---------------------------------------------------------------------------

_model: "_ST | None" = None


def _get_model() -> "_ST":
    """Devuelve el modelo SBERT, cargándolo en memoria solo una vez."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Cargando modelo Sentence-BERT '%s'...", MODEL_NAME)
            _model = SentenceTransformer(MODEL_NAME)
            logger.info("Modelo cargado correctamente.")
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers no está instalado. "
                "Ejecuta: pip install sentence-transformers"
            ) from exc
    return _model


# ---------------------------------------------------------------------------
# Funciones matemáticas (se conservan del stub — son correctas)
# ---------------------------------------------------------------------------

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Similitud coseno entre dos vectores de embeddings.

    Returns:
        Valor entre -1.0 y 1.0. Valores > 0.75 indican alta similitud semántica.
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def centroid(vectors: list[list[float]]) -> list[float]:
    """Calcula el centroide (promedio) de una lista de vectores.

    Útil para representar un cluster como un único vector promedio,
    permitiendo clasificar nuevos documentos por similitud al centroide.

    Returns:
        Vector promedio. Si la lista está vacía, devuelve vector de ceros.
    """
    if not vectors:
        return [0.0] * VECTOR_SIZE
    size = len(vectors[0])
    result = [0.0] * size
    for vec in vectors:
        for i, val in enumerate(vec):
            result[i] += val
    return [v / len(vectors) for v in result]


# ---------------------------------------------------------------------------
# Servicio principal de embeddings
# ---------------------------------------------------------------------------

class EmbeddingService:
    """Genera embeddings semánticos usando Sentence-BERT local.

    Uso básico:
        service = EmbeddingService()
        vector = service.embed("Redes de computadoras y protocolos TCP/IP")
        # → list[float] de 384 dimensiones

    El modelo se carga en la primera llamada y permanece en memoria.
    Los embeddings individuales se cachean por texto limpio para evitar
    recalcular el mismo documento varias veces en una sesión.
    """

    def __init__(self) -> None:
        self._cache: dict[str, list[float]] = {}

    def embed(self, text: str) -> list[float]:
        """Genera el embedding semántico de un texto.

        El texto se limpia y trunca antes de pasarlo al modelo.
        El resultado se cachea para evitar cómputo redundante.

        Args:
            text: Texto crudo del documento (se limpia internamente).

        Returns:
            Vector de 384 floats. Vector de ceros si el texto está vacío.
        """
        cleaned = truncate_for_embedding(clean_text(text))

        if not cleaned:
            logger.debug("Texto vacío tras limpieza, devolviendo vector cero.")
            return [0.0] * VECTOR_SIZE

        if cleaned in self._cache:
            return self._cache[cleaned]

        model = _get_model()
        vector: list[float] = model.encode(
            cleaned,
            normalize_embeddings=True,   # L2-norm → coseno == producto punto
            show_progress_bar=False,
        ).tolist()

        self._cache[cleaned] = vector
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para una lista de textos de forma eficiente.

        Procesa en lotes para aprovechar paralelismo interno de PyTorch.
        Los textos ya cacheados no se recomputan.

        Args:
            texts: Lista de textos crudos.

        Returns:
            Lista de vectores en el mismo orden que `texts`.
        """
        cleaned_texts = [truncate_for_embedding(clean_text(t)) for t in texts]

        # Separar los que ya están en caché de los que hay que computar
        to_encode_indices = [
            i for i, t in enumerate(cleaned_texts)
            if t and t not in self._cache
        ]
        to_encode_texts = [cleaned_texts[i] for i in to_encode_indices]

        if to_encode_texts:
            model = _get_model()
            logger.debug("Encodificando %d documentos nuevos...", len(to_encode_texts))
            new_vectors = model.encode(
                to_encode_texts,
                batch_size=BATCH_SIZE,
                normalize_embeddings=True,
                show_progress_bar=len(to_encode_texts) > 10,
            )
            for idx, vec in zip(to_encode_indices, new_vectors):
                self._cache[cleaned_texts[idx]] = vec.tolist()

        # Reconstruir resultados en orden original
        results: list[list[float]] = []
        for t in cleaned_texts:
            if t and t in self._cache:
                results.append(self._cache[t])
            else:
                results.append([0.0] * VECTOR_SIZE)
        return results

    def clear_cache(self) -> None:
        """Libera la caché en memoria (útil entre sesiones largas)."""
        self._cache.clear()
        logger.debug("Caché de embeddings liberada.")


# ---------------------------------------------------------------------------
# Instancia global reutilizable (patrón singleton ligero)
# ---------------------------------------------------------------------------

_default_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Devuelve la instancia global del servicio de embeddings."""
    global _default_service
    if _default_service is None:
        _default_service = EmbeddingService()
    return _default_service


def get_embedding(text: str) -> list[float]:
    """Atajo funcional para obtener el embedding de un texto.

    Equivalente a `get_embedding_service().embed(text)`.
    Es la función que llama directamente el controller.py.
    """
    return get_embedding_service().embed(text)