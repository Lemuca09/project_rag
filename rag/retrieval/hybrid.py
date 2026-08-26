"""Busca híbrida: TF-IDF (denso) + BM25 (esparso) fundidos com RRF."""

from __future__ import annotations

from rag.config import Settings
from rag.store.index import RagIndex, RetrievedHit


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[int, float]]],
    *,
    k: int,
) -> dict[int, float]:
    fused: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, (idx, _score) in enumerate(ranked, start=1):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank)
    return fused


def hybrid_search(
    index: RagIndex,
    query: str,
    settings: Settings,
) -> list[RetrievedHit]:
    query_vec = index.embedder.transform([query])[0]
    dense = index.vector.search(query_vec, settings.retrieve_top_k)
    sparse = index.bm25.search(query, settings.retrieve_top_k)
    fused = reciprocal_rank_fusion([dense, sparse], k=settings.rrf_k)

    dense_map = dict(dense)
    sparse_map = dict(sparse)
    hits: list[RetrievedHit] = []
    for idx, rrf in fused.items():
        dense_score = dense_map.get(idx, 0.0)
        sparse_score = sparse_map.get(idx, 0.0)
        weighted = (
            settings.hybrid_dense_weight * dense_score
            + settings.hybrid_sparse_weight * _minmax_one(sparse_score, sparse)
        )
        hits.append(
            RetrievedHit(
                chunk=index.chunks[idx],
                dense_score=dense_score,
                sparse_score=sparse_score,
                rrf_score=rrf + 0.05 * weighted,
            )
        )
    hits.sort(key=lambda h: h.rrf_score, reverse=True)
    return hits[: settings.retrieve_top_k]


def _minmax_one(value: float, pairs: list[tuple[int, float]]) -> float:
    if not pairs:
        return 0.0
    scores = [s for _, s in pairs]
    lo, hi = min(scores), max(scores)
    if hi <= lo:
        return 0.0
    return (value - lo) / (hi - lo)
