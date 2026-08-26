"""Rerank e diversificação MMR."""

from __future__ import annotations

import re

from rag.dedup import jaccard
from rag.store.index import RetrievedHit
from rag.text import normalize, tokenize
from rag.vocab.frames import QuestionFrame, parse_frame


def rerank(
    query: str,
    hits: list[RetrievedHit],
    *,
    top_k: int,
    mmr_lambda: float = 0.7,
    frame: QuestionFrame | None = None,
) -> list[RetrievedHit]:
    if not hits:
        return []
    q_tokens = tokenize(query)
    q_set = set(q_tokens)
    dense_vals = [h.dense_score for h in hits]
    sparse_vals = [h.sparse_score for h in hits]
    rrf_vals = [h.rrf_score for h in hits]
    frame = frame or parse_frame(query)

    for hit in hits:
        d_tokens = tokenize(hit.chunk.text)
        d_set = set(d_tokens)
        overlap = len(q_set & d_set) / max(len(q_set), 1)
        coverage = sum(1 for t in q_tokens if t in d_set) / max(len(q_tokens), 1)
        phrase = 1.0 if query.lower() in hit.chunk.text.lower() else 0.0
        period = _period_align(frame, hit)
        hit.rerank_score = (
            0.24 * _norm(hit.dense_score, dense_vals)
            + 0.20 * _norm(hit.sparse_score, sparse_vals)
            + 0.16 * _norm(hit.rrf_score, rrf_vals)
            + 0.16 * overlap
            + 0.10 * coverage
            + 0.04 * phrase
            + 0.10 * period
        )
    hits.sort(key=lambda h: h.rerank_score or 0.0, reverse=True)
    return diversify(hits, top_k=top_k, mmr_lambda=mmr_lambda)


def diversify(hits: list[RetrievedHit], *, top_k: int, mmr_lambda: float = 0.7) -> list[RetrievedHit]:
    if len(hits) <= 1:
        return hits[:top_k]
    selected: list[RetrievedHit] = []
    remaining = list(hits)
    while remaining and len(selected) < top_k:
        best = None
        best_score = -1.0
        for hit in remaining:
            rel = hit.rerank_score or 0.0
            sim = 0.0
            if selected:
                sim = max(jaccard(hit.chunk.text, s.chunk.text) for s in selected)
            mmr = mmr_lambda * rel - (1.0 - mmr_lambda) * sim
            if mmr > best_score:
                best_score = mmr
                best = hit
        if best is None:
            break
        selected.append(best)
        remaining = [h for h in remaining if h is not best]
    return selected


def _norm(value: float, values: list[float]) -> float:
    if not values:
        return 0.0
    lo, hi = min(values), max(values)
    if hi <= lo:
        return 0.0
    return (value - lo) / (hi - lo)


def _period_align(frame: QuestionFrame, hit: RetrievedHit) -> float:
    """1.0 se o chunk é do trimestre/ano pedido; 0 se é outro trimestre; 0.4 se neutro."""
    blob = " ".join(
        [
            hit.chunk.metadata.get("period", ""),
            hit.chunk.metadata.get("metric", ""),
            hit.chunk.text[:400],
        ]
    )
    n = normalize(blob)
    compact = n.replace(" ", "")
    if frame.period_n is not None:
        want = f"q{frame.period_n}"
        has_q = want in compact
        other_q = any(f"q{i}" in compact for i in range(1, 5) if i != frame.period_n)
        year_ok = (not frame.year) or frame.year in n
        if has_q and year_ok:
            return 1.0
        if other_q or (has_q and not year_ok):
            return 0.0
        return 0.35
    if frame.year:
        if frame.year in n:
            return 1.0
        if re.search(r"20\d{2}", n):
            return 0.1
        return 0.35
    return 0.4
