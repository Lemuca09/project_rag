"""Escolhe frases dos chunks recuperados."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rag.dedup import containment, is_near_duplicate, jaccard
from rag.store.index import RetrievedHit
from rag.text import normalize, split_sentences, tokenize
from rag.vocab.frames import parse_frame

_SPECIFIC = re.compile(
    r"(\d|r\$|%|prazo|deve|devem|obrigat|vedad|proibid|mínim|minim|"
    r"máxim|maxim|até |ate |após|apos |vedado|permitid|antecedência|"
    r"antecedencia|dias|horas|reais)",
    re.IGNORECASE,
)
_WEAK_LINKS = {
    "sistema",
    "documento",
    "politica",
    "interno",
    "manual",
}
_GENERIC = re.compile(
    r"^(documento de exemplo|manual interno|veja também|introdução|"
    r"neste documento|o presente)\b",
    re.IGNORECASE,
)


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
) -> str:
    if not hits:
        return "Não encontrei trechos relevantes no índice para essa pergunta."
    frame = parse_frame(question)
    q_terms = set(tokenize(question))
    q_terms -= set(frame.drop)
    if frame.year:
        q_terms.add(frame.year)
    if frame.period_n is not None:
        q_terms.add(f"q{frame.period_n}")
    candidates = _candidate_spans(q_terms, hits, frame=frame)
    if not candidates:
        return (
            "Não encontrei trechos que respondam essa pergunta com evidência suficiente. "
            "Reformule com o produto, o período ou o documento."
        )
    picked = _mmr_select(
        candidates,
        max_spans=max_spans,
        mmr_lambda=mmr_lambda,
        dup_threshold=dup_threshold,
    )
    lines = [span.text for span in picked]
    sources = list(dict.fromkeys(span.source for span in picked))
    return " ".join(lines) + "\n\nFontes: " + ", ".join(sources)


def _candidate_spans(
    q_terms: set[str],
    hits: list[RetrievedHit],
    *,
    frame,
) -> list[ExtractedSpan]:
    spans: list[ExtractedSpan] = []
    for hit in hits:
        src = hit.chunk.metadata.get("source_name", hit.chunk.source)
        section = hit.chunk.metadata.get("section") or ""
        period = hit.chunk.metadata.get("period") or ""
        for sentence in _hit_spans(hit):
            if _GENERIC.search(sentence.strip()):
                continue
            score = _span_score(q_terms, sentence, section, frame=frame, period=period)
            if score <= 0:
                continue
            spans.append(ExtractedSpan(text=sentence, source=src, score=score))
    spans.sort(key=lambda s: s.score, reverse=True)
    return spans


def _hit_spans(hit: RetrievedHit) -> list[str]:
    if hit.chunk.metadata.get("kind") == "table_fact":
        for block in hit.chunk.text.split("\n\n"):
            line = block.strip()
            if line and not line.startswith("#") and not line.startswith("|"):
                return [line]
        return [hit.chunk.text.strip()]
    return split_sentences(hit.chunk.text)


_MONEY = {"faturamento", "fatur", "receita", "ganho", "ganhamos", "lucro", "valor"}
_MONEY_HIT = {"faturamento", "fatur", "receita", "ganho", "ganhamos", "lucro", "pipeline", "arr", "ticket"}
_MONEY_RX = re.compile(r"r\$", re.IGNORECASE)
_PEOPLE_Q = {
    "funcionarios",
    "funcionario",
    "pessoas",
    "pessoa",
    "colaboradores",
    "colaborador",
    "trabalham",
    "trabalha",
    "headcount",
}
_PEOPLE_HIT = _PEOPLE_Q | {"headcount"}


def _span_score(
    q_terms: set[str],
    sentence: str,
    section: str,
    *,
    frame,
    period: str,
) -> float:
    s_terms = set(tokenize(sentence))
    if not s_terms:
        return 0.0
    blob = normalize(sentence + " " + period)
    compact = blob.replace(" ", "")
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
    people_q = bool(q_terms & _PEOPLE_Q)
    if people_q:
        if "soma clientes" in blob or "geridos no helios" in blob:
            return 0.0
        if "headcount" not in blob and "pessoas" not in s_terms:
            return 0.0
    if "meta" in q_terms and "meta" not in s_terms and "meta" not in blob:
        return 0.0
    if q_terms & _MONEY:
        moneyish = bool(s_terms & _MONEY_HIT) or bool(_MONEY_RX.search(sentence))
        if not moneyish:
            return 0.0
    overlap_terms = q_terms & s_terms
    if (q_terms & _MONEY) and (s_terms & _MONEY_HIT):
        overlap_terms = set(overlap_terms) | (s_terms & _MONEY_HIT)
    if people_q and (s_terms & _PEOPLE_HIT or "headcount" in blob):
        overlap_terms = set(overlap_terms) | (s_terms & _PEOPLE_HIT) | (q_terms & _PEOPLE_Q)
    overlap = len(overlap_terms)
    if overlap == 0 and section:
        overlap_terms = q_terms & set(tokenize(section))
        overlap = len(overlap_terms) * 0.4
        if overlap == 0:
            return 0.0
    elif overlap == 0:
        return 0.0
    if overlap < 2:
        only = next(iter(overlap_terms)) if overlap_terms else ""
        if only in _WEAK_LINKS or (len(str(only)) <= 4 and not str(only).isdigit()):
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
    if "headcount" in blob and (frame is None or not frame.year):
        if "2026" in blob:
            period_mul *= 1.25
        elif "2025" in blob:
            period_mul *= 1.08
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
