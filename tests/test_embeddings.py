"""Pruebas para embeddings y similitud semantica local."""

from __future__ import annotations

import unittest

from ai.embeddings import VECTOR_SIZE, EmbeddingService, cosine_similarity


class EmbeddingServiceTest(unittest.TestCase):
    def test_embed_returns_fixed_size_vector(self) -> None:
        vector = EmbeddingService().embed("hola mundo")
        self.assertEqual(len(vector), VECTOR_SIZE)

    def test_related_sentences_are_more_similar_than_unrelated_sentences(self) -> None:
        service = EmbeddingService()
        left = service.embed("red neuronal algoritmo aprendizaje profundo")
        right = service.embed("aprendizaje profundo con red neuronal y algoritmo")
        unrelated = service.embed("consultas sql y normalizacion de bases de datos")

        self.assertGreater(cosine_similarity(left, right), cosine_similarity(left, unrelated))


if __name__ == "__main__":
    unittest.main()
