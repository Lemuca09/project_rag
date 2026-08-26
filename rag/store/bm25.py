"""Índice BM25 Okapi."""

from __future__ import annotations

import math

import numpy as np

from rag.text import tokenize


class BM25Index:
    def __init__(
        self,
        documents: list[str],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.k1 = k1
        self.b = b
        self._tokens = [tokenize(doc) for doc in documents]
        self.n_docs = len(self._tokens)
        self.doc_len = np.array([len(toks) for toks in self._tokens], dtype=np.float64)
        self.avgdl = float(self.doc_len.mean()) if self.n_docs else 0.0
        df: dict[str, int] = {}
        for toks in self._tokens:
            for term in set(toks):
                df[term] = df.get(term, 0) + 1
        self.idf = {
            term: math.log((self.n_docs - freq + 0.5) / (freq + 0.5) + 1.0)
            for term, freq in df.items()
        }

    def search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        q_terms = tokenize(query)
        if not q_terms or self.n_docs == 0:
            return []
        scores = np.zeros(self.n_docs, dtype=np.float64)
        for i, toks in enumerate(self._tokens):
            if not toks:
                continue
            tf: dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            dl = self.doc_len[i]
            score = 0.0
            for term in q_terms:
                freq = tf.get(term, 0)
                if freq == 0:
                    continue
                idf = self.idf.get(term, 0.0)
                denom = freq + self.k1 * (1.0 - self.b + self.b * dl / max(self.avgdl, 1e-9))
                score += idf * (freq * (self.k1 + 1.0)) / denom
            scores[i] = score
        k = min(top_k, self.n_docs)
        idx = np.argpartition(scores, -k)[-k:]
        idx = idx[np.argsort(scores[idx])[::-1]]
        return [(int(i), float(scores[i])) for i in idx if scores[i] > 0]
