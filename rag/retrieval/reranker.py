"""Rerank e diversificação MMR."""

from __future__ import annotations

import re

from rag.dedup import jaccard
from rag.retrieval.route import recency_score, source_route_score
from rag.store.index import RetrievedHit
from rag.text import normalize, tokenize
from rag.vocab.cooccur import TermGraph
from rag.vocab.frames import QuestionFrame, parse_frame


def rerank(
    query: str,
    hits: list[RetrievedHit],
    *,
    top_k: int,
    mmr_lambda: float = 0.7,
    frame: QuestionFrame | None = None,
    route_query: str | None = None,
    latest_year: str | None = None,
    graph: TermGraph | None = None,
) -> list[RetrievedHit]:
    if not hits:
        return []
    q_tokens = tokenize(query)
    q_set = set(q_tokens)
    dense_vals = [h.dense_score for h in hits]
    sparse_vals = [h.sparse_score for h in hits]
    rrf_vals = [h.rrf_score for h in hits]
    frame = frame or parse_frame(query)
    asked = route_query or query
    drop = set(frame.drop)

    for hit in hits:
        d_tokens = tokenize(hit.chunk.text)
        d_set = set(d_tokens)
        overlap = len(q_set & d_set) / max(len(q_set), 1)
        coverage = sum(1 for t in q_tokens if t in d_set) / max(len(q_tokens), 1)
        phrase = 1.0 if query.lower() in hit.chunk.text.lower() else 0.0
        period = _period_align(frame, hit, latest_year=latest_year)
        route = source_route_score(asked, hit, drop=drop, graph=graph)
        metric = _metric_align(asked, hit, graph)
        hit.rerank_score = (
            0.16 * _norm(hit.dense_score, dense_vals)
            + 0.14 * _norm(hit.sparse_score, sparse_vals)
            + 0.10 * _norm(hit.rrf_score, rrf_vals)
            + 0.10 * overlap
            + 0.06 * coverage
            + 0.04 * phrase
            + 0.12 * period
            + 0.14 * route
            + 0.14 * metric
        )

    _penalize_off_route(hits, asked, drop, graph)
    hits.sort(key=lambda h: h.rerank_score or 0.0, reverse=True)
    if frame.kind == "procedure":
        mmr_lambda = max(mmr_lambda, 0.86)
    return diversify(hits, top_k=top_k, mmr_lambda=mmr_lambda)


def _penalize_off_route(
    hits: list[RetrievedHit],
    asked: str,
    drop: set[str],
    graph: TermGraph | None,
) -> None:
    """Se um arquivo/seção casa forte com a pergunta, não misturar fontes só de passagem."""
    routes = [source_route_score(asked, hit, drop=drop, graph=graph) for hit in hits]
    if not routes:
        return
    best = max(routes)
    if best < 0.7:
        return
    for hit, route in zip(hits, routes):
        if route < 0.5 and hit.rerank_score is not None:
            hit.rerank_score *= 0.22


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


def _period_align(
    frame: QuestionFrame,
    hit: RetrievedHit,
    *,
    latest_year: str | None = None,
) -> float:
    """1.0 se o chunk é do trimestre/ano pedido; sem ano, prefere o mais recente do corpus."""
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
    return recency_score(hit, query_year=None, latest_year=latest_year)


def _metric_align(query: str, hit: RetrievedHit, graph: TermGraph | None) -> float:
    """Cruza os termos da pergunta (e vizinhos do índice) com a métrica/seção do chunk."""
    from rag.retrieval.route import content_terms

    q = content_terms(query, graph=graph)
    if not q:
        return 0.5
    neighbors: set[str] = set()
    if graph and graph.n_docs:
        neighbors = set(graph.expand(list(q), k=8))
    want = q | neighbors
    loc = set(
        tokenize(
            " ".join(
                [
                    hit.chunk.metadata.get("metric", ""),
                    hit.chunk.metadata.get("section", ""),
                    hit.chunk.text[:360],
                ]
            )
        )
    )
    return min(1.0, len(want & loc) / max(len(q), 1))
