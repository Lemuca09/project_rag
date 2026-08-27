"""Documento da pergunta e recência quando o ano não vem na query."""

from __future__ import annotations

import re

from rag.ingest.chunker import Chunk
from rag.store.index import RetrievedHit
from rag.text import FILLER_PT, tokenize
from rag.vocab.cooccur import TermGraph

_YEAR_RX = re.compile(r"20\d{2}")


def content_terms(
    query: str,
    extra_drop: set[str] | None = None,
    *,
    graph: TermGraph | None = None,
) -> set[str]:
    drop = set(FILLER_PT) | (extra_drop or set())
    out: set[str] = set()
    for token in tokenize(query):
        if token in drop:
            continue
        if graph is not None and graph.is_common(token, max_df=0.28):
            continue
        if len(token) > 2 or re.fullmatch(r"q[1-4]", token):
            out.add(token)
    return out


def years_in_text(*parts: str) -> list[int]:
    blob = " ".join(p for p in parts if p)
    return [int(y) for y in _YEAR_RX.findall(blob)]


def max_year(*parts: str) -> int | None:
    found = years_in_text(*parts)
    return max(found) if found else None


def hit_year(hit: RetrievedHit) -> int | None:
    md = hit.chunk.metadata
    named = max_year(md.get("source_name", ""), md.get("period", ""), md.get("metric", ""))
    if named:
        return named
    return max_year(hit.chunk.text[:500])


def scan_latest_year(chunks: list[Chunk]) -> str | None:
    years: list[int] = []
    for chunk in chunks:
        md = chunk.metadata
        years.extend(years_in_text(md.get("period", ""), md.get("metric", ""), chunk.text[:400]))
    return str(max(years)) if years else None


def source_route_score(
    query: str,
    hit: RetrievedHit,
    *,
    drop: set[str] | None = None,
    graph: TermGraph | None = None,
) -> float:
    """1.0 se o arquivo/seção é o lugar da pergunta; baixo se só cita o termo de passagem."""
    terms = content_terms(query, drop, graph=graph)
    if not terms:
        return 0.5
    name = hit.chunk.metadata.get("source_name") or hit.chunk.source
    name = name.replace("\\", "/").split("/")[-1]
    name = name.replace("_", " ").replace("-", " ").replace(".md", "")
    section = hit.chunk.metadata.get("section") or ""
    metric = hit.chunk.metadata.get("metric") or ""
    period = hit.chunk.metadata.get("period") or ""
    name_toks = set(tokenize(name))
    sec_toks = set(tokenize(" ".join((section, metric, period))))
    head_toks = set(tokenize(hit.chunk.text[:480]))
    name_ov = len(terms & name_toks)
    sec_ov = len(terms & sec_toks)
    text_ov = len(terms & head_toks)
    if name_ov:
        return min(1.0, 0.72 + 0.28 * min(name_ov, 2))
    if sec_ov:
        return min(1.0, 0.58 + 0.22 * min(sec_ov, 2))
    if text_ov:
        return min(0.42, 0.14 * text_ov)
    return 0.04


def recency_score(
    hit: RetrievedHit,
    *,
    query_year: str | None,
    latest_year: str | None,
) -> float:
    year = hit_year(hit)
    if query_year:
        if year is None:
            return 0.4
        return 1.0 if str(year) == query_year else 0.12
    if year is None:
        return 0.5
    if latest_year and str(year) == latest_year:
        return 1.0
    if latest_year:
        gap = int(latest_year) - year
        if gap <= 0:
            return 1.0
        return max(0.08, 1.0 - 0.32 * gap)
    return 0.4
