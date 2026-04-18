"""Extracción de palabras clave con TF-IDF y filtrado morfológico (spaCy).

Estrategia de dos capas:
  1. TF-IDF sobre el corpus completo para pesar relevancia relativa.
  2. Filtrado por categoría gramatical (POS) con spaCy para quedarnos
     solo con sustantivos, adjetivos y nombres propios.

Si spaCy no está instalado o el modelo no existe, degrada graciosamente
a TF-IDF puro sin filtrado morfológico.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from typing import Protocol

from ai.text_utils import clean_text, token_frequencies, detect_language

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# POS tags de spaCy que consideramos keywords válidas
_VALID_POS = {"NOUN", "PROPN", "ADJ", "VERB"}

# Número máximo de keywords por documento
DEFAULT_LIMIT = 12

# Mínima frecuencia en el corpus para incluir un término en el IDF
_MIN_DOC_FREQ = 1

# Keywords técnicos de alta prioridad (siempre incluir)
TECH_KEYWORDS = {
    "machine", "learning", "deep", "neural", "tensorflow", "pytorch",
    "sql", "mysql", "postgresql", "oracle", "mongodb",
    "network", "router", "switch", "tcp", "ip", "dns", "dhcp",
    "docker", "kubernetes", "virtual", "vmware", "proxmox",
    "aws", "azure", "gcp", "cloud",
    "pentest", "exploit", "metasploit", "nmap",
}


# ---------------------------------------------------------------------------
# Carga lazy de spaCy (opcional — degrada si no está)
# ---------------------------------------------------------------------------

def _load_spacy(lang: str = "es"):
    """Carga el modelo spaCy correcto según idioma detectado.

    Intenta cargar:
      - Español: es_core_news_sm
      - Inglés:  en_core_web_sm

    Si falla, retorna None y el extractor usa modo sin POS.
    """
    model_map = {"es": "es_core_news_sm", "en": "en_core_web_sm"}
    model_name = model_map.get(lang, "es_core_news_sm")
    try:
        import spacy
        return spacy.load(model_name)
    except Exception:
        logger.warning(
            "Modelo spaCy '%s' no disponible. "
            "Instala con: python -m spacy download %s\n"
            "Fallback: TF-IDF sin filtrado POS.",
            model_name, model_name,
        )
        return None


# ---------------------------------------------------------------------------
# Motor TF-IDF mínimo (sin dependencias externas)
# ---------------------------------------------------------------------------

class _TFIDFEngine:
    """Calcula TF-IDF sobre un corpus de documentos.

    TF  (Term Frequency):     frecuencia del término en el documento.
    IDF (Inverse Doc Freq):   log(N / df(t) + 1) — penaliza palabras
                               que aparecen en muchos documentos.
    """

    def __init__(self) -> None:
        self._doc_freq: Counter[str] = Counter()   # en cuántos docs aparece cada término
        self._n_docs: int = 0

    def fit(self, corpus: list[str]) -> None:
        """Construye el IDF a partir de un corpus de textos limpios."""
        self._n_docs = len(corpus)
        self._doc_freq.clear()
        for text in corpus:
            unique_tokens = set(token_frequencies(text).keys())
            self._doc_freq.update(unique_tokens)


    def score(self, text: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        tf = token_frequencies(text)
        if not tf:
            return []

        n = max(self._n_docs, 1)
        vowels = set("aeiouáéíóúü")
        scored: list[tuple[str, float]] = []
        
        for term, freq in tf.items():
            term_lower = term.lower()
            
            # ✅ Filtros de calidad
            if len(term) < 3:
                continue
            if not term.isalpha():
                continue
            vowel_ratio = sum(1 for ch in term if ch in vowels) / len(term)
            if vowel_ratio < 0.15:          # menos vocales = menos strict
                continue
            if term.isupper() and len(term) <= 3:   # solo 2-3 letras mayúsculas
                continue

            # ✅ Boost para keywords técnicos
            boost = 1.0
            if term_lower in TECH_KEYWORDS:
                boost = 3.0  # Prioridad 3x
            
            df = self._doc_freq.get(term, 0) + 1
            idf = math.log(n / df) + 1
            score = freq * idf * boost
            scored.append((term, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [term for term, _ in scored[:limit]]

    @property
    def is_fitted(self) -> bool:
        return self._n_docs > 0


# ---------------------------------------------------------------------------
# Extractor principal
# ---------------------------------------------------------------------------

class KeywordExtractor:
    """Extrae keywords relevantes de un documento usando TF-IDF + spaCy POS.

    Uso básico (un solo documento):
        extractor = KeywordExtractor()
        keywords = extractor.extract("Análisis de redes TCP/IP en IPv4")
        # → ["redes", "analisis", "protocolos", ...]

    Uso con corpus (recomendado para mejor calidad):
        extractor = KeywordExtractor()
        extractor.fit_corpus(all_texts)   # una sola vez
        keywords = extractor.extract(doc_text)
    """

    def __init__(self) -> None:
        self._tfidf = _TFIDFEngine()
        self._nlp_es = None   # cargado lazy
        self._nlp_en = None   # cargado lazy
        self._spacy_available = True

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def fit_corpus(self, texts: list[str]) -> None:
        """Entrena el IDF sobre el corpus completo.

        Llamar una sola vez antes de procesar documentos individuales.
        Si no se llama, el extractor funciona con TF puro (menos preciso).

        Args:
            texts: Lista de textos crudos de todos los documentos.
        """
        cleaned = [clean_text(t) for t in texts if t]
        self._tfidf.fit(cleaned)
        logger.info("IDF entrenado sobre %d documentos.", len(cleaned))

    def extract(self, text: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        """Extrae las keywords más relevantes de un documento.

        Pipeline:
        1. Limpia el texto con `clean_text`.
        2. Puntúa con TF-IDF (penaliza palabras comunes del corpus).
        3. Filtra por POS con spaCy (solo sustantivos y adjetivos).
        4. Devuelve los `limit` mejores términos.

        Args:
            text: Texto crudo del documento.
            limit: Número máximo de keywords a retornar.

        Returns:
            Lista de keywords ordenadas por relevancia (mayor → menor).
        """
        if not text or not text.strip():
            return []

        cleaned = clean_text(text)

        # Paso 1: candidatos por TF-IDF (obtenemos más para luego filtrar)
        candidates = self._tfidf.score(cleaned, limit=limit * 3)

        if not candidates:
            freq = token_frequencies(cleaned)
            # ✅ Filtrar tokens cortos y muy genéricos
            candidates = [
                t for t, _ in freq.most_common(limit * 3)
                if len(t) >= 4  # descartar palabras de 1-3 letras
            ]

        # Paso 2: filtrar por POS con spaCy (si disponible)
        lang = detect_language(cleaned)
        filtered = self._filter_by_pos(candidates, cleaned, lang)

        # Si el filtro POS eliminó demasiado, usar candidatos originales
        result = filtered if len(filtered) >= min(3, limit) else candidates

        return result[:limit]

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _get_nlp(self, lang: str):
        """Retorna el modelo spaCy cargado para el idioma dado."""
        if not self._spacy_available:
            return None

        if lang == "en":
            if self._nlp_en is None:
                self._nlp_en = _load_spacy("en")
                if self._nlp_en is None:
                    self._spacy_available = False
            return self._nlp_en
        else:
            if self._nlp_es is None:
                self._nlp_es = _load_spacy("es")
                if self._nlp_es is None:
                    self._spacy_available = False
            return self._nlp_es

    def _filter_by_pos(
        self,
        candidates: list[str],
        full_text: str,
        lang: str,
    ) -> list[str]:
        """Filtra candidatos conservando solo sustantivos y adjetivos.

        Parsea el texto completo con spaCy y construye un set de tokens
        con POS válido. Luego intersecta con los candidatos TF-IDF.

        Args:
            candidates: Tokens candidatos ordenados por TF-IDF.
            full_text: Texto limpio completo (para el análisis POS).
            lang: Código de idioma ("es" o "en").

        Returns:
            Subconjunto de candidates con POS válido, manteniendo orden.
        """
        nlp = self._get_nlp(lang)
        if nlp is None:
            return candidates  # sin filtrado si spaCy no está

        try:
            doc = nlp(full_text[:10_000])   # spaCy tiene límite interno
            valid_lemmas: set[str] = {
                token.lemma_.lower()
                for token in doc
                if token.pos_ in _VALID_POS
                and not token.is_stop
                and len(token.lemma_) >= 3
            }
            # Conservar el orden de relevancia TF-IDF
            return [c for c in candidates if c in valid_lemmas]
        except Exception as exc:
            logger.warning("Error en análisis POS de spaCy: %s", exc)
            return candidates