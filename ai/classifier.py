"""Clasificación de archivos nuevos por similitud con clusters existentes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.embeddings import cosine_similarity, centroid
from config.settings import DEFAULT_SIMILARITY_THRESHOLD

if TYPE_CHECKING:
    from core.models import FileRecord

logger = logging.getLogger(__name__)

# FIX: usar threshold de settings (0.70) en lugar del hardcodeado 0.50
_DEFAULT_THRESHOLD = DEFAULT_SIMILARITY_THRESHOLD


class DocumentClassifier:
    """Clasifica un documento nuevo dentro de los clusters existentes.

    Estrategia:
    1. Compara el embedding del doc con el centroide de cada categoría.
    2. Si el mejor score supera el umbral → asigna esa categoría.
    3. Si no supera el umbral pero hay una categoría claramente mejor
       (gap > 0.10 sobre la segunda) → asigna igual con score bajo.
    4. Si hay empate o score muy bajo → retorna None (sin clasificar).
    """
# ai/classifier.py — reemplaza solo el método classify()

def classify(
    self,
    embedding: list[float],
    category_vectors: dict[str, list[float]],
    *,
    similarity_threshold: float = _DEFAULT_THRESHOLD,
) -> tuple[str | None, float]:
    if not embedding or not category_vectors:
        return None, 0.0

    scores: list[tuple[float, str]] = []
    for label, cat_vector in category_vectors.items():
        if not cat_vector or all(v == 0.0 for v in cat_vector):
            continue
        score = cosine_similarity(embedding, cat_vector)
        scores.append((score, label))

    if not scores:
        return None, 0.0

    scores.sort(reverse=True)
    best_score, best_label = scores[0]

    # ✅ Umbral reducido al 80% del configurado para ser menos estricto
    effective_threshold = similarity_threshold * 0.80

    # Supera umbral directo
    if best_score >= effective_threshold:
        logger.debug("Clasificado como '%s' (score=%.3f)", best_label, best_score)
        return best_label, best_score

    # ✅ Única categoría: asignar con score >= 0.30 (antes 0.40)
    if len(scores) == 1 and best_score >= 0.30:
        logger.debug(
            "Única categoría '%s' con score %.3f — asignando",
            best_label, best_score,
        )
        return best_label, best_score

    # ✅ Margen reducido a 0.08 (antes 0.12) y score mínimo a 0.35 (antes 0.45)
    if len(scores) >= 2 and best_score >= 0.35:
        second_score = scores[1][0]
        if best_score - second_score >= 0.08:
            logger.debug(
                "Clasificado '%s' por margen (score=%.3f, gap=%.3f)",
                best_label, best_score, best_score - second_score,
            )
            return best_label, best_score

    logger.debug(
        "Clasificación descartada — mejor score %.3f < umbral efectivo %.3f",
        best_score, effective_threshold,
    )
    return None, best_score

    def classify_against_clusters(
        self,
        record: "FileRecord",
        groups: dict[int, list["FileRecord"]],
        *,
        similarity_threshold: float = _DEFAULT_THRESHOLD,
    ) -> int:
        if not groups:
            return 0

        cluster_centroids: dict[int, list[float]] = {
            cid: centroid([r.embedding for r in members])
            for cid, members in groups.items()
        }

        best_id: int = -1
        best_score = 0.0

        for cid, centroid_vec in cluster_centroids.items():
            score = cosine_similarity(record.embedding, centroid_vec)
            if score > best_score:
                best_id = cid
                best_score = score

        if best_score >= similarity_threshold and best_id >= 0:
            logger.debug(
                "Archivo '%s' → cluster %d (score=%.3f)",
                record.name, best_id, best_score,
            )
            return best_id

        new_id = max(groups.keys()) + 1
        logger.debug(
            "Archivo '%s' sin cluster similar → singleton %d",
            record.name, new_id,
        )
        return new_id


def classify_file(
    record: "FileRecord",
    clusters: dict[int, list["FileRecord"]],
) -> int:
    classifier = DocumentClassifier()
    return classifier.classify_against_clusters(record, clusters)