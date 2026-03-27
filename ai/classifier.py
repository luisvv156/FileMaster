"""Clasificacion de archivos por similitud con categorias existentes."""

from __future__ import annotations

from ai.embeddings import cosine_similarity


class DocumentClassifier:
    def classify(
        self,
        embedding: list[float],
        category_vectors: dict[str, list[float]],
        *,
        similarity_threshold: float = 0.42,
    ) -> tuple[str | None, float]:
        best_label = None
        best_score = 0.0
        for label, category_vector in category_vectors.items():
            score = cosine_similarity(embedding, category_vector)
            if score > best_score:
                best_label = label
                best_score = score

        if best_label is None or best_score < similarity_threshold:
            return None, best_score
        return best_label, best_score
