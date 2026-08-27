"""Avalia trechos e resposta: relevância, fundamentação e repetição."""

from __future__ import annotations

from dataclasses import dataclass, field

from rag.dedup import answer_redundancy
from rag.dedup import jaccard
from rag.store.index import RetrievedHit
from rag.text import FILLER_PT, normalize, tokenize, unique_terms
from rag.vocab.cooccur import TermGraph
from rag.vocab.frames import parse_frame


@dataclass
class QualityReport:
    ok: bool
    score: float
    missing_terms: list[str] = field(default_factory=list)
    hint: str = ""
    reasons: list[str] = field(default_factory=list)


@dataclass
class AnswerVerdict:
    ok: bool
    score: float
    grounded: bool
    reasons: list[str] = field(default_factory=list)


class QualityGate:
    def __init__(
        self,
        min_score: float = 0.55,
        max_redundancy: float = 0.82,
    ) -> None:
        self.min_score = min_score
        self.max_redundancy = max_redundancy

    def evaluate_retrieval(
        self,
        query: str,
        hits: list[RetrievedHit],
        graph: TermGraph | None = None,
    ) -> QualityReport:
        return _heuristic_retrieval(query, hits, self.min_score, graph=graph)

    def verify_answer(
        self,
        query: str,
        answer: str,
        hits: list[RetrievedHit],
        graph: TermGraph | None = None,
    ) -> AnswerVerdict:
        return _heuristic_answer(query, answer, hits, self.max_redundancy, graph=graph)


def _term_in_blob(term: str, blob: str, graph: TermGraph | None = None) -> bool:
    if term in blob:
        return True
    if graph is None:
        return False
    return any(nb in blob for nb, _w in graph.neighbors.get(term, [])[:8])


def _heuristic_retrieval(
    query: str,
    hits: list[RetrievedHit],
    min_score: float,
    graph: TermGraph | None = None,
) -> QualityReport:
    if not hits:
        return QualityReport(
            ok=False,
            score=0.0,
            missing_terms=unique_terms(query),
            hint="nenhum trecho retornado; tente termos mais específicos",
            reasons=["índice vazio ou query sem match"],
        )
    frame = parse_frame(query)
    q_terms = [
        t
        for t in unique_terms(query)
        if t not in FILLER_PT
        and t not in frame.drop
        and not (graph is not None and graph.is_common(t, max_df=0.15))
    ]
    blob = " ".join(normalize(h.chunk.text) for h in hits)
    present = [t for t in q_terms if _term_in_blob(t, blob, graph)]
    missing = [t for t in q_terms if not _term_in_blob(t, blob, graph)]
    coverage = len(present) / max(len(q_terms), 1)
    top = hits[0].rerank_score if hits[0].rerank_score is not None else hits[0].rrf_score
    pair_sims = []
    for i, a in enumerate(hits):
        for b in hits[i + 1 :]:
            pair_sims.append(jaccard(a.chunk.text, b.chunk.text))
    diversity = 1.0 - (sum(pair_sims) / len(pair_sims) if pair_sims else 0.0)
    score = 0.50 * coverage + 0.35 * min(max(top, 0.0), 1.0) + 0.15 * diversity
    reasons = [
        f"cobertura de termos={coverage:.2f}",
        f"score do topo={top:.3f}",
        f"diversidade dos trechos={diversity:.2f}",
    ]
    hint = ""
    if missing:
        hint = "buscar também: " + ", ".join(missing[:8])
        reasons.append("termos ausentes: " + ", ".join(missing[:8]))
    return QualityReport(
        ok=score >= min_score,
        score=score,
        missing_terms=missing,
        hint=hint,
        reasons=reasons,
    )


def _heuristic_answer(
    query: str,
    answer: str,
    hits: list[RetrievedHit],
    max_redundancy: float,
    graph: TermGraph | None = None,
) -> AnswerVerdict:
    if not answer.strip():
        return AnswerVerdict(ok=False, score=0.0, grounded=False, reasons=["resposta vazia"])
    ctx = " ".join(normalize(h.chunk.text) for h in hits)
    a_terms = tokenize(answer)
    if not a_terms:
        return AnswerVerdict(ok=False, score=0.0, grounded=False, reasons=["resposta sem termos"])
    supported = sum(1 for t in a_terms if t in ctx)
    grounded_ratio = supported / len(a_terms)
    ans_blob = normalize(answer)
    frame = parse_frame(query)
    q_terms = [
        t
        for t in unique_terms(query)
        if t not in FILLER_PT
        and t not in frame.drop
        and not (graph is not None and graph.is_common(t, max_df=0.15))
    ]
    answered = sum(1 for t in q_terms if _term_in_blob(t, ans_blob, graph)) / max(len(q_terms), 1)
    redundancy = answer_redundancy(answer)
    frame_ok = True
    if frame.kind in {"quantity_period", "quantity"}:
        frame_ok = any(ch.isdigit() for ch in answer)
        if frame.year:
            frame_ok = frame_ok and frame.year in ans_blob
    elif frame.kind == "definition":
        frame_ok = len(tokenize(answer)) >= 8
    elif frame.year:
        frame_ok = frame.year in ans_blob
    grounded = grounded_ratio >= 0.45
    unique_ok = redundancy < max_redundancy
    score = (
        0.45 * grounded_ratio
        + 0.25 * answered
        + 0.15 * (1.0 - redundancy)
        + 0.15 * (1.0 if frame_ok else 0.0)
    )
    reasons = [
        f"termos da resposta presentes no contexto={grounded_ratio:.2f}",
        f"cobertura da pergunta na resposta={answered:.2f}",
        f"redundância entre frases={redundancy:.2f}",
        f"quadro={frame.kind} ok={frame_ok}",
    ]
    if not unique_ok:
        reasons.append("frases extraídas demais parecidas; extração foi considerada repetida")
    if not frame_ok:
        reasons.append("a resposta não fecha o quadro da pergunta (período/quantidade vs. definição)")
    return AnswerVerdict(
        ok=grounded and unique_ok and frame_ok and score >= 0.45,
        score=score,
        grounded=grounded,
        reasons=reasons,
    )
