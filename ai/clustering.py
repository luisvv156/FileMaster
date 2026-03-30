"""Clustering semántico de documentos con DBSCAN sobre embeddings SBERT.

Reemplaza el stub con similitud coseno precalculada y contrato correcto
con el controller (retorna dict[int, list[FileRecord]]).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.embeddings import cosine_similarity, centroid, VECTOR_SIZE

if TYPE_CHECKING:
    from core.models import FileRecord

logger = logging.getLogger(__name__)
# ---------------------------------------------------------------------------
# Constantes — calibradas para embeddings SBERT normalizados
# ---------------------------------------------------------------------------
DEFAULT_SIMILARITY   = 0.65   # Umbral coseno para considerar docs "vecinos"
DEFAULT_MIN_SAMPLES  = 2      # Mínimo de vecinos para formar un cluster
NOISE_LABEL          = -1     # Etiqueta interna para ruido antes de reasignar


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class DocumentClusterer:
    """Agrupa documentos por similitud semántica usando DBSCAN.

    Opera sobre vectores de embeddings (384-dim SBERT). Los documentos
    que no pertenecen a ningún cluster se convierten en singletons
    (cada uno en su propio grupo) en lugar de marcarse como ruido.

    Uso básico:
        clusterer = DocumentClusterer()
        labels = clusterer.cluster(embeddings)
        # → [0, 0, 1, 1, 2, 3, 3, ...]   (un int por documento)
    """

    def cluster(
        self,
        embeddings: list[list[float]],
        *,
        similarity_threshold: float = DEFAULT_SIMILARITY,
        min_samples: int = DEFAULT_MIN_SAMPLES,
    ) -> list[int]:
        """Ejecuta DBSCAN y retorna un label por documento.

        Args:
            embeddings: Lista de vectores (uno por documento).
            similarity_threshold: Similitud coseno mínima para considerar
                dos documentos como vecinos (0.0–1.0). Para SBERT se
                recomienda 0.60–0.70.
            min_samples: Mínimo de documentos para formar un cluster real.
                Documentos solos se convierten en singletons.

        Returns:
            Lista de enteros donde cada índice corresponde al documento en
            `embeddings`. Valores ≥ 0 son IDs de cluster. No hay -1 en el
            resultado final (los documentos sin cluster son singletons).
        """
        n = len(embeddings)
        if n == 0:
            return []
        if n == 1:
            return [0]

        logger.info(
            "DBSCAN: %d documentos, umbral=%.2f, min_samples=%d",
            n, similarity_threshold, min_samples,
        )

        sim_matrix = _build_similarity_matrix(embeddings)
        labels   = [NOISE_LABEL] * n
        visited  = [False] * n
        cluster_id = 0

        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True

            region = _neighbors(i, sim_matrix, similarity_threshold)

            if len(region) < min_samples:
                continue

            labels[i] = cluster_id
            # ✅ Fix: usar set para O(1) en el `in`
            seeds_set  = set(region) - {i}
            seeds_list = list(seeds_set)
            cursor = 0

            while cursor < len(seeds_list):
                candidate = seeds_list[cursor]

                if not visited[candidate]:
                    visited[candidate] = True
                    candidate_region = _neighbors(
                        candidate, sim_matrix, similarity_threshold
                    )
                    if len(candidate_region) >= min_samples:
                        for neighbor in candidate_region:
                            if neighbor not in seeds_set:   # O(1) ahora
                                seeds_set.add(neighbor)
                                seeds_list.append(neighbor)

                if labels[candidate] == NOISE_LABEL:
                    labels[candidate] = cluster_id

                cursor += 1

            cluster_id += 1

        # Reasignar ruido como singletons
        for i, label in enumerate(labels):
            if label == NOISE_LABEL:
                labels[i] = cluster_id
                cluster_id += 1

        logger.info(
            "Clustering completado: %d clusters (%d documentos).",
            len(set(labels)), n,
        )
        return labels


# ---------------------------------------------------------------------------
# Función pública que consume el controller.py
# ---------------------------------------------------------------------------

def cluster_files(records: list["FileRecord"]) -> dict[int, list["FileRecord"]]:
    """Agrupa FileRecords por similitud semántica de sus embeddings.

    Args:
        records: FileRecords con `embedding` ya calculado.

    Returns:
        Diccionario {cluster_id: [FileRecord, ...]}. Muta cada record
        asignando su `cluster_id`.
    """
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
    """Calcula el centroide de embeddings para cada cluster.

    Usado por el classifier para asignar nuevos documentos al grupo
    más cercano por similitud coseno.
    """
    return {
        cid: centroid([r.embedding for r in members])
        for cid, members in groups.items()
    }
# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _build_similarity_matrix(
    embeddings: list[list[float]],
) -> list[list[float]]:
    """Construye la matriz de similitud coseno N×N (precalculada una sola vez)."""
    n = len(embeddings)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        matrix[i][i] = 1.0
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            matrix[i][j] = sim
            matrix[j][i] = sim
    return matrix


def _neighbors(
    index: int,
    sim_matrix: list[list[float]],
    threshold: float,
) -> list[int]:
    """Retorna los índices de todos los vecinos de `index` en la matriz."""
    row = sim_matrix[index]
    return [j for j, sim in enumerate(row) if sim >= threshold]