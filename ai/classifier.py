"""Clasificación de archivos nuevos por similitud con clusters existentes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.embeddings import centroid, cosine_similarity
from config.settings import DEFAULT_SIMILARITY_THRESHOLD

if TYPE_CHECKING:
    from core.models import FileRecord

logger = logging.getLogger(__name__)

_DEFAULT_THRESHOLD = DEFAULT_SIMILARITY_THRESHOLD


class DocumentClassifier:
    """Clasifica documentos basándose en similitud semántica."""

    def classify(
        self,
        embedding: list[float],
        category_vectors: dict[str, list[float]],
        *,
        similarity_threshold: float | None = None,
    ) -> tuple[str | None, float]:
        if not embedding or not category_vectors:
            return None, 0.0

        threshold = similarity_threshold or _DEFAULT_THRESHOLD
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

        if best_score >= threshold:
            return best_label, best_score

        if len(scores) >= 2:
            second_score = scores[1][0]
            gap = best_score - second_score
            if best_score >= 0.50 and gap >= 0.15:
                return best_label, best_score

        if len(scores) == 1 and best_score >= 0.55:
            return best_label, best_score

        logger.debug(
            "Sin clasificación clara, best=%.3f < threshold=%.3f",
            best_score,
            threshold,
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
            return best_id

        return max(groups.keys()) + 1


def classify_file(
    record: "FileRecord",
    clusters: dict[int, list["FileRecord"]],
) -> int:
    classifier = DocumentClassifier()
    return classifier.classify_against_clusters(record, clusters)
