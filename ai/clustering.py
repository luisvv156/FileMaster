"""DBSCAN simplificado basado en similitud coseno."""

from __future__ import annotations

from ai.embeddings import cosine_similarity


class DocumentClusterer:
    def cluster(
        self,
        embeddings: list[list[float]],
        *,
        similarity_threshold: float = 0.28,
        min_samples: int = 2,
    ) -> list[int]:
        if not embeddings:
            return []

        labels = [-99] * len(embeddings)
        visited = [False] * len(embeddings)
        cluster_id = 0

        def neighbors(index: int) -> list[int]:
            return [
                candidate
                for candidate, vector in enumerate(embeddings)
                if cosine_similarity(embeddings[index], vector) >= similarity_threshold
            ]

        for index in range(len(embeddings)):
            if visited[index]:
                continue

            visited[index] = True
            region = neighbors(index)
            if len(region) < min_samples:
                labels[index] = -1
                continue

            labels[index] = cluster_id
            seeds = [candidate for candidate in region if candidate != index]
            cursor = 0
            while cursor < len(seeds):
                candidate = seeds[cursor]
                if not visited[candidate]:
                    visited[candidate] = True
                    candidate_region = neighbors(candidate)
                    if len(candidate_region) >= min_samples:
                        for neighbor in candidate_region:
                            if neighbor not in seeds:
                                seeds.append(neighbor)
                if labels[candidate] in {-99, -1}:
                    labels[candidate] = cluster_id
                cursor += 1
            cluster_id += 1

        next_singleton = cluster_id
        for index, label in enumerate(labels):
            if label == -1:
                labels[index] = next_singleton
                next_singleton += 1

        return labels
