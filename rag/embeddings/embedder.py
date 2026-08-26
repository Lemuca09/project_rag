"""Embedder TF-IDF."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from rag.text import tokenize


class TfidfEmbedder:
    """Vetoriza textos com TF-IDF + L2."""

    def __init__(self, min_df: int = 1, max_df: float = 0.95) -> None:
        self.min_df = min_df
        self.max_df = max_df
        self.vocab: dict[str, int] = {}
        self.idf: np.ndarray | None = None
        self.n_docs = 0

    @property
    def dim(self) -> int:
        return len(self.vocab)

    def fit(self, texts: list[str]) -> TfidfEmbedder:
        df: dict[str, int] = {}
        n = len(texts)
        for text in texts:
            for term in set(tokenize(text)):
                df[term] = df.get(term, 0) + 1
        max_df_count = max(int(self.max_df * n), 1) if n else 1
        terms = [
            t
            for t, c in sorted(df.items())
            if c >= self.min_df and c <= max_df_count
        ]
        if not terms:
            terms = sorted(df.keys()) or ["_empty"]
        self.vocab = {t: i for i, t in enumerate(terms)}
        self.n_docs = n
        idf = np.zeros(len(terms), dtype=np.float32)
        for t, i in self.vocab.items():
            idf[i] = math.log((n + 1) / (df.get(t, 0) + 1)) + 1.0
        self.idf = idf
        return self

    def transform(self, texts: list[str]) -> np.ndarray:
        if self.idf is None or not self.vocab:
            raise RuntimeError("TfidfEmbedder precisa de fit() antes de transform()")
        matrix = np.zeros((len(texts), len(self.vocab)), dtype=np.float32)
        for row, text in enumerate(texts):
            counts: dict[int, int] = {}
            tokens = tokenize(text)
            if not tokens:
                continue
            for term in tokens:
                idx = self.vocab.get(term)
                if idx is not None:
                    counts[idx] = counts.get(idx, 0) + 1
            length = len(tokens)
            for idx, tf in counts.items():
                matrix[row, idx] = (tf / length) * self.idf[idx]
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        return self.fit(texts).transform(texts)

    def encode(self, texts: list[str], *, show_progress: bool = False) -> np.ndarray:
        del show_progress
        return self.transform(texts)

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "min_df": self.min_df,
                    "max_df": self.max_df,
                    "n_docs": self.n_docs,
                    "vocab": self.vocab,
                    "idf": (self.idf.tolist() if self.idf is not None else []),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> TfidfEmbedder:
        data = json.loads(path.read_text(encoding="utf-8"))
        embedder = cls(min_df=data["min_df"], max_df=data["max_df"])
        embedder.n_docs = data["n_docs"]
        embedder.vocab = {str(k): int(v) for k, v in data["vocab"].items()}
        embedder.idf = np.asarray(data["idf"], dtype=np.float32)
        return embedder
