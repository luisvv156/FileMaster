"""Pruebas para el clusterizador local estilo DBSCAN."""

from __future__ import annotations

import unittest

from ai.clustering import DocumentClusterer
from ai.embeddings import EmbeddingService


class DocumentClustererTest(unittest.TestCase):
    def test_cluster_groups_related_documents(self) -> None:
        service = EmbeddingService()
        embeddings = [
            service.embed("red neuronal algoritmo aprendizaje profundo"),
            service.embed("modelo de aprendizaje profundo con red neuronal"),
            service.embed("consulta sql joins normalizacion de tablas"),
        ]

        labels = DocumentClusterer().cluster(embeddings, similarity_threshold=0.2, min_samples=2)

        self.assertEqual(len(labels), 3)
        self.assertEqual(labels[0], labels[1])
        self.assertNotEqual(labels[0], labels[2])


if __name__ == "__main__":
    unittest.main()
