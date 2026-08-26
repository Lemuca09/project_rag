"""Grafo de coocorrência no índice."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from rag.text import tokenize


class TermGraph:
    """Vizinhos de cada termo segundo os chunks ingeridos (PMI-lite por contagem)."""

    def __init__(self) -> None:
        self.neighbors: dict[str, list[tuple[str, float]]] = {}
        self.df: dict[str, int] = {}
        self.n_docs = 0

    def fit(self, texts: list[str]) -> TermGraph:
        pair: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        df: dict[str, int] = defaultdict(int)
        n = 0
        for text in texts:
            terms = list(dict.fromkeys(tokenize(text)))
            if len(terms) < 2:
                continue
            n += 1
            for t in terms:
                df[t] += 1
            for i, a in enumerate(terms):
                for b in terms[i + 1 :]:
                    pair[a][b] += 1
                    pair[b][a] += 1
        self.n_docs = n
        self.df = dict(df)
        neigh: dict[str, list[tuple[str, float]]] = {}
        for term, others in pair.items():
            scored: list[tuple[str, float]] = []
            for other, c in others.items():
                idf = _idf(self.n_docs, df.get(other, 1))
                scored.append((other, c * idf))
            scored.sort(key=lambda x: x[1], reverse=True)
            neigh[term] = scored[:24]
        self.neighbors = neigh
        return self

    def has(self, term: str) -> bool:
        return term in self.neighbors or term in self.df

    def expand(self, terms: list[str], *, k: int = 8) -> list[str]:
        weights: dict[str, float] = {}
        seed = set(terms)
        for term in terms:
            for other, w in self.neighbors.get(term, [])[:k]:
                if other in seed:
                    continue
                weights[other] = weights.get(other, 0.0) + w
        ranked = sorted(weights, key=lambda t: weights[t], reverse=True)
        return ranked[:k]

    def neighbor_set(self, term: str, *, k: int = 12) -> set[str]:
        return {t for t, _w in self.neighbors.get(term, [])[:k]}

    def sense_clash(self, token: str, context_terms: list[str], *, k: int = 12) -> bool:
        """True se o sentido dominante do token no índice não combina com o resto da pergunta."""
        token_nb = self.neighbor_set(token, k=k)
        if not token_nb:
            return False
        ctx_nb: set[str] = set()
        for t in context_terms:
            if t == token:
                continue
            ctx_nb |= self.neighbor_set(t, k=k)
            ctx_nb.add(t)
        if not ctx_nb:
            return False
        overlap = len(token_nb & ctx_nb)
        return overlap <= 1

    def save(self, path: Path) -> None:
        payload = {
            "n_docs": self.n_docs,
            "df": self.df,
            "neighbors": {t: [[a, w] for a, w in pairs] for t, pairs in self.neighbors.items()},
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> TermGraph:
        graph = cls()
        if not path.exists():
            return graph
        data = json.loads(path.read_text(encoding="utf-8"))
        graph.n_docs = int(data.get("n_docs", 0))
        graph.df = {str(k): int(v) for k, v in data.get("df", {}).items()}
        raw = data.get("neighbors", {})
        graph.neighbors = {
            str(t): [(str(a), float(w)) for a, w in pairs] for t, pairs in raw.items()
        }
        return graph


def _idf(n_docs: int, df: int) -> float:
    from math import log

    return log((n_docs + 1) / (df + 1)) + 1.0
