"""Clasificación de archivos nuevos por similitud con clusters existentes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.embeddings import cosine_similarity, centroid

if TYPE_CHECKING:
    from core.models import FileRecord

logger = logging.getLogger(__name__)

# Umbral mínimo para aceptar una clasificación como válida
_DEFAULT_THRESHOLD = 0.50


class DocumentClassifier:
    """Clasifica un documento nuevo dentro de los clusters existentes.

    Compara el embedding del documento con el centroide de cada cluster
    y asigna el cluster con mayor similitud coseno. Si ningún cluster
    supera el umbral, retorna None (el documento se marca como sin clasificar).

    Uso básico:
        classifier = DocumentClassifier()
        label, score = classifier.classify(
            embedding=record.embedding,
            category_vectors={"redes": [...], "programacion": [...]},
        )
    """

    def classify(
        self,
        embedding: list[float],
        category_vectors: dict[str, list[float]],
        *,
        similarity_threshold: float = _DEFAULT_THRESHOLD,
    ) -> tuple[str | None, float]:
        """Clasifica un embedding contra vectores de categoría.

        Args:
            embedding: Vector del documento a clasificar.
            category_vectors: Mapa {nombre_categoria: vector_centroide}.
            similarity_threshold: Similitud mínima para aceptar clasificación.

        Returns:
            Tupla (categoria, score). Si no supera el umbral → (None, score).
        """
        if not embedding or not category_vectors:
            return None, 0.0

        best_label: str | None = None
        best_score = 0.0

        for label, cat_vector in category_vectors.items():
            score = cosine_similarity(embedding, cat_vector)
            if score > best_score:
                best_label = label
                best_score = score

        if best_score < similarity_threshold:
            logger.debug(
                "Clasificación descartada — mejor score %.3f < umbral %.3f",
                best_score, similarity_threshold,
            )
            return None, best_score

        logger.debug("Clasificado como '%s' (score=%.3f)", best_label, best_score)
        return best_label, best_score

    def classify_against_clusters(
        self,
        record: "FileRecord",
        groups: dict[int, list["FileRecord"]],
        *,
        similarity_threshold: float = _DEFAULT_THRESHOLD,
    ) -> int:
        """Asigna un FileRecord al cluster más similar.

        Opera sobre los grupos reales (salida de cluster_files()) en lugar
        de vectores precalculados. Calcula el centroide de cada grupo
        internamente y clasifica por similitud.

        Args:
            record: FileRecord con `embedding` ya calculado.
            groups: Salida de clustering.cluster_files().
            similarity_threshold: Umbral mínimo de similitud.

        Returns:
            cluster_id asignado. Si no supera umbral, crea un nuevo grupo
            singleton con el ID más alto + 1.
        """
        if not groups:
            return 0

        # Calcular centroides de cada grupo
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

        # Sin cluster suficientemente similar → singleton nuevo
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
    """Función libre que usa directamente el controller.py.

    Args:
        record: FileRecord con embedding calculado.
        clusters: Grupos existentes (salida de cluster_files).

    Returns:
        cluster_id asignado.
    """
    classifier = DocumentClassifier()
    return classifier.classify_against_clusters(record, clusters)