"""Clustering semántico de documentos con DBSCAN sobre embeddings SBERT."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.embeddings import cosine_similarity, centroid, VECTOR_SIZE
from config.settings import DEFAULT_CLUSTERING_THRESHOLD

if TYPE_CHECKING:
    from core.models import FileRecord

logger = logging.getLogger(__name__)

# EXTREME: más estricto para mejor precisión
DEFAULT_SIMILARITY = 0.45  # Balance strict
DEFAULT_MIN_SAMPLES = 1   # Allow smaller groups
NOISE_LABEL = -1


class DocumentClusterer:
    # ✅ cluster() ahora SÍ está dentro de la clase (indentado)
    def cluster(
        self,
        embeddings: list[list[float]],
        *,
        similarity_threshold: float = DEFAULT_SIMILARITY,
        min_samples: int = DEFAULT_MIN_SAMPLES,
    ) -> list[int]:
        n = len(embeddings)
        if n == 0:
            return []
        if n == 1:
            return [0]

        # Usar siempre el mismo umbral para consistencia
        effective_min = 1 if n < 10 else min(min_samples, max(1, n // 5))
        effective_threshold = similarity_threshold

        logger.info(
            "DBSCAN: %d documentos, umbral=%.2f, min_samples=%d",
            n, effective_threshold, effective_min,
        )

        sim_matrix = _build_similarity_matrix(embeddings)
        labels     = [NOISE_LABEL] * n
        visited    = [False] * n
        cluster_id = 0

        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True
            region = _neighbors(i, sim_matrix, effective_threshold)

            if len(region) < effective_min:
                continue

            labels[i] = cluster_id
            seeds_set  = set(region) - {i}
            seeds_list = list(seeds_set)
            cursor = 0

            while cursor < len(seeds_list):
                candidate = seeds_list[cursor]
                if not visited[candidate]:
                    visited[candidate] = True
                    candidate_region = _neighbors(candidate, sim_matrix, effective_threshold)
                    if len(candidate_region) >= effective_min:
                        for neighbor in candidate_region:
                            if neighbor not in seeds_set:
                                seeds_set.add(neighbor)
                                seeds_list.append(neighbor)
                if labels[candidate] == NOISE_LABEL:
                    labels[candidate] = cluster_id
                cursor += 1

            cluster_id += 1

        for i, label in enumerate(labels):
            if label == NOISE_LABEL:
                labels[i] = cluster_id
                cluster_id += 1

        n_clusters = len(set(labels))
        logger.info("Clustering completado: %d clusters (%d documentos).", n_clusters, n)
        return labels


# ✅ Estas funciones sí van fuera de la clase (son funciones libres)
def cluster_files(records: list["FileRecord"]) -> dict[int, list["FileRecord"]]:
    if not records:
        return {}
    embeddings = [r.embedding for r in records]
    labels = DocumentClusterer().cluster(embeddings)
    groups: dict[int, list["FileRecord"]] = {}
    for record, label in zip(records, labels):
        record.cluster_id = label
        groups.setdefault(label, []).append(record)
    logger.info("cluster_files: %d archivos → %d grupos.", len(records), len(groups))
    return groups


def cluster_centroids(
    groups: dict[int, list["FileRecord"]],
) -> dict[int, list[float]]:
    return {
        cid: centroid([r.embedding for r in members])
        for cid, members in groups.items()
    }


def _build_similarity_matrix(embeddings: list[list[float]]) -> list[list[float]]:
    n = len(embeddings)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        matrix[i][i] = 1.0
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            matrix[i][j] = sim
            matrix[j][i] = sim
    return matrix


def _neighbors(index: int, sim_matrix: list[list[float]], threshold: float) -> list[int]:
    row = sim_matrix[index]
    return [j for j, sim in enumerate(row) if sim >= threshold]