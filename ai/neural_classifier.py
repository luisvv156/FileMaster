"""Clasificador experto para categorias de FileMaster.

Arquitectura:
- Feature union: TF-IDF de palabras + TF-IDF de caracteres.
- Ensemble ponderado: Logistic Regression + Linear SVM calibrado + MLP.
- Entrenamiento con rebalanceo y aumentacion ligera por categoria.
"""

from __future__ import annotations

import logging
import random
import re
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_RANDOM_SEED = 42
_MIN_CLASSES = 2
_MIN_SAMPLES_TOTAL = 12
_MIN_SAMPLES_PER_CLASS = 3
_MAX_TEXT_CHARS = 4500


@dataclass
class NeuralPrediction:
    label: str | None
    confidence: float = 0.0


class NeuralCategoryClassifier:
    """Clasificador tipo experto con ensamble de modelos."""

    def __init__(self) -> None:
        self._ready = False
        self._vectorizer = None
        self._models: dict[str, object] = {}
        self._classes: list[str] = []
        self._weights: dict[str, float] = {
            "lr": 0.38,
            "svm": 0.37,
            "mlp": 0.25,
        }

    @property
    def ready(self) -> bool:
        return self._ready

    def fit(self, samples: list[tuple[str, str]]) -> bool:
        texts, labels = self._normalize_samples(samples)
        if len(texts) < _MIN_SAMPLES_TOTAL:
            self._ready = False
            return False
        label_counts = defaultdict(int)
        for label in labels:
            label_counts[label] += 1
        if len(label_counts) < _MIN_CLASSES:
            self._ready = False
            return False
        if min(label_counts.values()) < _MIN_SAMPLES_PER_CLASS:
            texts, labels = self._augment_and_rebalance(texts, labels)

        try:
            from sklearn.calibration import CalibratedClassifierCV
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.neural_network import MLPClassifier
            from sklearn.pipeline import FeatureUnion
            from sklearn.svm import LinearSVC
        except Exception as exc:
            logger.warning("Expert neural desactivado (sklearn no disponible): %s", exc)
            self._ready = False
            return False

        try:
            word_tfidf = TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                ngram_range=(1, 2),
                max_features=5000,
                min_df=1,
                sublinear_tf=True,
            )
            char_tfidf = TfidfVectorizer(
                lowercase=True,
                analyzer="char_wb",
                ngram_range=(3, 5),
                max_features=4000,
                min_df=1,
                sublinear_tf=True,
            )
            self._vectorizer = FeatureUnion(
                [("word", word_tfidf), ("char", char_tfidf)],
            )
            x = self._vectorizer.fit_transform(texts)
        except Exception as exc:
            logger.warning("No se pudo vectorizar para expert neural: %s", exc)
            self._ready = False
            return False

        self._models = {}
        self._classes = sorted(set(labels))

        try:
            lr = LogisticRegression(
                max_iter=1200,
                class_weight="balanced",
                random_state=_RANDOM_SEED,
                n_jobs=None,
            )
            lr.fit(x, labels)
            self._models["lr"] = lr
        except Exception as exc:
            logger.debug("Fallo LogisticRegression: %s", exc)

        try:
            base_svm = LinearSVC(
                class_weight="balanced",
                random_state=_RANDOM_SEED,
            )
            svm = CalibratedClassifierCV(base_svm, method="sigmoid", cv=3)
            svm.fit(x, labels)
            self._models["svm"] = svm
        except Exception as exc:
            logger.debug("Fallo LinearSVC calibrado: %s", exc)

        try:
            mlp = MLPClassifier(
                hidden_layer_sizes=(256, 96),
                activation="relu",
                solver="adam",
                alpha=8e-5,
                learning_rate_init=8e-4,
                max_iter=420,
                random_state=_RANDOM_SEED,
                early_stopping=True,
                validation_fraction=0.15,
                n_iter_no_change=16,
            )
            mlp.fit(x, labels)
            self._models["mlp"] = mlp
        except Exception as exc:
            logger.debug("Fallo MLP: %s", exc)

        self._ready = bool(self._models)
        logger.info(
            "Expert neural entrenado | muestras=%d | clases=%d | modelos=%s",
            len(texts),
            len(self._classes),
            ",".join(sorted(self._models.keys())) or "ninguno",
        )
        return self._ready

    def predict(self, text: str) -> NeuralPrediction:
        if not self._ready or not text or self._vectorizer is None:
            return NeuralPrediction(None, 0.0)
        try:
            cleaned = self._clean_text(text)
            x = self._vectorizer.transform([cleaned])
        except Exception as exc:
            logger.debug("Vectorizacion en predict fallo: %s", exc)
            return NeuralPrediction(None, 0.0)

        pooled: dict[str, float] = {label: 0.0 for label in self._classes}
        weight_sum = 0.0
        for name, model in self._models.items():
            weight = float(self._weights.get(name, 0.0))
            if weight <= 0.0:
                continue
            try:
                if not hasattr(model, "predict_proba"):
                    continue
                probs = model.predict_proba(x)[0]
                classes = [str(c) for c in model.classes_]
                for cls, prob in zip(classes, probs):
                    pooled[cls] = pooled.get(cls, 0.0) + (float(prob) * weight)
                weight_sum += weight
            except Exception as exc:
                logger.debug("Modelo %s fallo en predict: %s", name, exc)

        if weight_sum <= 0.0 or not pooled:
            return NeuralPrediction(None, 0.0)
        for cls in list(pooled.keys()):
            pooled[cls] = pooled[cls] / weight_sum

        ordered = sorted(pooled.items(), key=lambda item: item[1], reverse=True)
        best_label, best_prob = ordered[0]
        second_prob = ordered[1][1] if len(ordered) > 1 else 0.0
        margin = max(0.0, best_prob - second_prob)

        confidence = min(0.995, (best_prob * 0.82) + (margin * 0.35))
        if margin < 0.05:
            confidence *= 0.88
        return NeuralPrediction(best_label, confidence)

    def _normalize_samples(self, samples: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
        texts: list[str] = []
        labels: list[str] = []
        for raw_text, raw_label in samples:
            text = self._clean_text(raw_text)
            label = str(raw_label).strip()
            if not text or not label:
                continue
            texts.append(text)
            labels.append(label)
        return texts, labels

    def _augment_and_rebalance(self, texts: list[str], labels: list[str]) -> tuple[list[str], list[str]]:
        rng = random.Random(_RANDOM_SEED)
        by_label: dict[str, list[str]] = defaultdict(list)
        for text, label in zip(texts, labels):
            by_label[label].append(text)

        target = max(max(len(items) for items in by_label.values()), _MIN_SAMPLES_PER_CLASS)
        out_texts = list(texts)
        out_labels = list(labels)

        for label, items in by_label.items():
            if not items:
                continue
            needed = max(0, target - len(items))
            if needed == 0:
                continue
            idx = 0
            while idx < needed:
                base = items[idx % len(items)]
                aug = self._augment_text(base, rng)
                out_texts.append(aug)
                out_labels.append(label)
                idx += 1
        return out_texts, out_labels

    def _augment_text(self, text: str, rng: random.Random) -> str:
        tokens = text.split()
        if len(tokens) > 6:
            start = rng.randint(0, max(0, len(tokens) // 4))
            end = rng.randint(max(start + 5, len(tokens) // 2), len(tokens))
            tokens = tokens[start:end]
        if len(tokens) > 8:
            head = tokens[: min(6, len(tokens))]
            tail = tokens[-min(6, len(tokens)) :]
            middle = tokens[min(3, len(tokens)) : -min(3, len(tokens))]
            rng.shuffle(middle)
            tokens = head + middle[:10] + tail
        return " ".join(tokens)[:_MAX_TEXT_CHARS]

    def _clean_text(self, text: str) -> str:
        clean = (text or "").lower()
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:_MAX_TEXT_CHARS]
