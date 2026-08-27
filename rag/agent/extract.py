"""Escolhe frases dos chunks recuperados."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rag.dedup import containment, is_near_duplicate, jaccard
from rag.retrieval.route import content_terms, max_year, source_route_score
from rag.store.index import RetrievedHit
from rag.text import FILLER_PT, normalize, split_sentences, tokenize
from rag.vocab.cooccur import TermGraph
from rag.vocab.frames import parse_frame

_SPECIFIC = re.compile(
    r"(\d|r\$|%|prazo|deve|devem|obrigat|vedad|proibid|mínim|minim|"
    r"máxim|maxim|até |ate |após|apos |vedado|permitid|antecedência|"
    r"antecedencia|dias|horas|reais)",
    re.IGNORECASE,
)
_GENERIC = re.compile(
    r"^(veja também|introdução|neste documento|o presente)\b",
    re.IGNORECASE,
)
_HOWTO_STEP = re.compile(
    r"(^\s*\d+[\.\)]|execute|obrigat|proibid|checklist|pare\b|deve|devem)",
    re.IGNORECASE,
)
_MONEY_RX = re.compile(r"r\$|\bmi\b", re.IGNORECASE)


@dataclass
class ExtractedSpan:
    text: str
    source: str
    score: float


def extract_answer(
    question: str,
    hits: list[RetrievedHit],
    *,
    max_spans: int = 3,
    mmr_lambda: float = 0.7,
    dup_threshold: float = 0.8,
    latest_year: str | None = None,
    extra_terms: list[str] | None = None,
    graph: TermGraph | None = None,
) -> str:
    if not hits:
        return "Não encontrei trechos relevantes no índice para essa pergunta."
    frame = parse_frame(question)
    q_terms = set(tokenize(question))
    q_terms -= set(frame.drop)
    q_terms -= set(FILLER_PT)
    q_terms |= {t for t in (extra_terms or []) if t not in FILLER_PT and t not in frame.drop}
    if frame.year:
        q_terms.add(frame.year)
    if frame.period_n is not None:
        q_terms.add(f"q{frame.period_n}")
    hits = _route_hits(question, hits, frame=frame, graph=graph)
    candidates = _candidate_spans(
        q_terms,
        hits,
        frame=frame,
        question=question,
        latest_year=latest_year,
        graph=graph,
    )
    if not candidates:
        return (
            "Não encontrei trechos que respondam essa pergunta com evidência suficiente. "
            "Reformule com o produto, o período ou o documento."
        )
    if frame.kind == "procedure":
        mmr_lambda = max(mmr_lambda, 0.86)
        max_spans = min(max_spans, 2)
    elif frame.kind in {"quantity", "quantity_period"}:
        max_spans = 1
    picked = _mmr_select(
        candidates,
        max_spans=max_spans,
        mmr_lambda=mmr_lambda,
        dup_threshold=dup_threshold,
    )
    lines = [span.text for span in picked]
    sources = list(dict.fromkeys(span.source for span in picked))
    return " ".join(lines) + "\n\nFontes: " + ", ".join(sources)


def _route_hits(
    question: str,
    hits: list[RetrievedHit],
    *,
    frame,
    graph: TermGraph | None,
) -> list[RetrievedHit]:
    drop = set(frame.drop)
    routes = [source_route_score(question, hit, drop=drop, graph=graph) for hit in hits]
    best = max(routes) if routes else 0.0
    if best < 0.7:
        return hits
    filtered = [h for h, r in zip(hits, routes) if r >= 0.5]
    return filtered or hits


def _candidate_spans(
    q_terms: set[str],
    hits: list[RetrievedHit],
    *,
    frame,
    question: str,
    latest_year: str | None,
    graph: TermGraph | None,
) -> list[ExtractedSpan]:
    spans: list[ExtractedSpan] = []
    distinctive = content_terms(question, set(frame.drop), graph=graph)
    for hit in hits:
        src = hit.chunk.metadata.get("source_name", hit.chunk.source)
        section = hit.chunk.metadata.get("section") or ""
        period = hit.chunk.metadata.get("period") or ""
        route = source_route_score(question, hit, drop=set(frame.drop), graph=graph)
        rel = hit.rerank_score if hit.rerank_score is not None else 0.5
        kind = hit.chunk.metadata.get("kind") or ""
        for sentence in _hit_spans(hit):
            if _GENERIC.search(sentence.strip()):
                continue
            if kind != "table_fact" and sentence.count(":") >= 3:
                continue
            score = _span_score(
                q_terms,
                sentence,
                section,
                frame=frame,
                period=period,
                source=src,
                distinctive=distinctive,
            )
            if score <= 0:
                continue
            score *= 0.45 + 0.55 * route
            score *= 0.55 + 0.45 * min(max(rel, 0.0), 1.0)
            spans.append(ExtractedSpan(text=sentence, source=src, score=score))
    spans.sort(key=lambda s: s.score, reverse=True)
    spans = _prefer_query_cores(spans, distinctive)
    return _keep_latest_year(spans, frame, latest_year)


def _prefer_query_cores(spans: list[ExtractedSpan], distinctive: set[str]) -> list[ExtractedSpan]:
    """Se algum trecho traz o substantivo da pergunta, fica só com esses. Senão, não força."""
    cores = {t for t in distinctive if not t.isdigit() and not re.fullmatch(r"q[1-4]", t)}
    if not cores or not spans:
        return spans
    with_core = []
    for span in spans:
        toks = set(tokenize(span.text)) | set(tokenize(span.source.replace("_", " ")))
        if cores & toks:
            with_core.append(span)
    return with_core or spans


def _keep_latest_year(
    spans: list[ExtractedSpan],
    frame,
    latest_year: str | None,
) -> list[ExtractedSpan]:
    if not spans or (frame is not None and frame.year):
        return spans
    if frame is not None and frame.kind == "procedure":
        return spans
    if frame is None or frame.kind not in {"quantity", "quantity_period"}:
        return spans
    years = [max_year(span.source) or max_year(span.text) for span in spans]
    present = [y for y in years if y]
    if not present:
        return spans
    want = max(present)
    if latest_year:
        ly = int(latest_year)
        if ly in present:
            want = ly
    dated = [span for span, year in zip(spans, years) if year == want]
    return dated or spans


def _hit_spans(hit: RetrievedHit) -> list[str]:
    if hit.chunk.metadata.get("kind") == "table_fact":
        for block in hit.chunk.text.split("\n\n"):
            line = block.strip()
            if line and not line.startswith("#") and not line.startswith("|"):
                return [line]
        return [hit.chunk.text.strip()]
    return split_sentences(hit.chunk.text)


def _span_score(
    q_terms: set[str],
    sentence: str,
    section: str,
    *,
    frame,
    period: str,
    source: str = "",
    distinctive: set[str] | None = None,
) -> float:
    s_terms = set(tokenize(sentence))
    if not s_terms:
        return 0.0
    blob = normalize(sentence + " " + period)
    compact = blob.replace(" ", "")
    sec_terms = set(tokenize(section))
    src_terms = set(tokenize(source.replace("_", " ").replace("-", " ").replace(".md", "")))
    if frame is not None and frame.period_n is not None:
        if f"q{frame.period_n}" not in compact:
            return 0.0
        if frame.year and frame.year not in blob:
            return 0.0
    elif frame is not None and frame.year and frame.year not in blob:
        return 0.0
    if frame is not None and frame.kind in {"quantity", "quantity_period"}:
        if not re.search(r"\d", sentence):
            return 0.0
    distinctive = distinctive or set()
    if frame is not None and frame.kind == "procedure" and distinctive:
        loc = s_terms | sec_terms | src_terms
        if not (distinctive & loc):
            return 0.0
    overlap_terms = q_terms & s_terms
    overlap = len(overlap_terms)
    if overlap == 0:
        loc = sec_terms | src_terms
        if loc & (q_terms | distinctive):
            overlap_terms = (q_terms | distinctive) & loc
            overlap = max(len(overlap_terms) * 0.5, 0.5)
        elif section:
            overlap_terms = q_terms & sec_terms
            overlap = len(overlap_terms) * 0.4
        if overlap == 0:
            return 0.0
    if len(overlap_terms) < 2:
        only = next(iter(overlap_terms)) if overlap_terms else ""
        if len(str(only)) <= 4 and not str(only).isdigit():
            return 0.0
    coverage = min(1.0, overlap / max(len(q_terms), 1))
    density = min(1.0, overlap / max(len(s_terms), 1))
    specific = 0.25 if _SPECIFIC.search(sentence) else 0.0
    length = len(sentence)
    if length < 40:
        length_pen = 0.35
    elif length > 420:
        length_pen = 0.55
    else:
        length_pen = 1.0
    period_mul = _period_mul(frame, sentence, period)
    if frame is not None and frame.kind in {"quantity", "quantity_period"} and not frame.people:
        if _MONEY_RX.search(sentence):
            period_mul *= 1.2
    if distinctive:
        period_mul *= 1.0 + 0.15 * len(distinctive & (s_terms | sec_terms))
        longest = max(distinctive, key=len)
        if longest in s_terms or longest in sec_terms:
            period_mul *= 1.35
    if frame is not None and frame.kind == "procedure":
        if _HOWTO_STEP.search(sentence):
            period_mul *= 1.45
        else:
            period_mul *= 0.5
    return (0.38 * coverage + 0.37 * density + specific) * length_pen * period_mul


def _period_mul(frame, sentence: str, period: str) -> float:
    if frame is None or frame.period_n is None:
        return 1.0
    blob = normalize(sentence + " " + period)
    compact = blob.replace(" ", "")
    want = f"q{frame.period_n}"
    year_ok = (not frame.year) or frame.year in blob
    if want in compact and year_ok:
        return 1.35
    if any(f"q{i}" in compact for i in range(1, 5) if i != frame.period_n):
        return 0.35
    return 0.85


def _mmr_select(
    candidates: list[ExtractedSpan],
    *,
    max_spans: int,
    mmr_lambda: float,
    dup_threshold: float,
) -> list[ExtractedSpan]:
    selected: list[ExtractedSpan] = []
    remaining = list(candidates)
    while remaining and len(selected) < max_spans:
        best: ExtractedSpan | None = None
        best_mmr = -1.0
        for cand in remaining:
            if is_near_duplicate(
                cand.text,
                [s.text for s in selected],
                threshold=dup_threshold,
            ):
                continue
            sim = 0.0
            if selected:
                sim = max(jaccard(cand.text, s.text) for s in selected)
                sim = max(sim, max(containment(cand.text, s.text) for s in selected))
            mmr = mmr_lambda * cand.score - (1.0 - mmr_lambda) * sim
            if mmr > best_mmr:
                best_mmr = mmr
                best = cand
        if best is None:
            break
        selected.append(best)
        remaining = [c for c in remaining if c is not best]
    return selected
