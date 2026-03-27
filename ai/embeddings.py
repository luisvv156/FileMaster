"""Embeddings locales mediante hashing de tokens."""

from __future__ import annotations

import hashlib
import math

from ai.text_utils import tokenize


VECTOR_SIZE = 96


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(left * right for left, right in zip(a, b))
    norm_a = math.sqrt(sum(value * value for value in a))
    norm_b = math.sqrt(sum(value * value for value in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def centroid(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return [0.0] * VECTOR_SIZE
    result = [0.0] * len(vectors[0])
    for vector in vectors:
        for idx, value in enumerate(vector):
            result[idx] += value
    return [value / len(vectors) for value in result]


class EmbeddingService:
    def embed(self, text: str) -> list[float]:
        vector = [0.0] * VECTOR_SIZE
        for token in tokenize(text):
            index = self._stable_index(token)
            vector[index] += 1.0
        return vector

    def _stable_index(self, token: str) -> int:
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "big") % VECTOR_SIZE
