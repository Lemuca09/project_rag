"""Reescreve a pergunta antes da busca."""

from __future__ import annotations

from dataclasses import dataclass, field

from rag.text import FILLER_PT, tokenize, unique_terms
from rag.vocab.cooccur import TermGraph
from rag.vocab.frames import QuestionFrame, parse_frame


@dataclass
class RewrittenQuery:
    original: str
    search_query: str
    keywords: list[str] = field(default_factory=list)
    reason: str = ""
    frame: QuestionFrame = field(default_factory=lambda: QuestionFrame(kind="generic"))


class QueryRewriter:
    def rewrite(
        self,
        question: str,
        *,
        history: list[str] | None = None,
        hint: str | None = None,
        graph: TermGraph | None = None,
    ) -> RewrittenQuery:
        frame = parse_frame(question)
        cleaned = " ".join(question.strip().split())
        tokens = tokenize(cleaned, drop_stopwords=False)
        kept = [t for t in tokens if t not in FILLER_PT and t not in frame.drop]
        if len(kept) < 2 and history:
            kept = list(dict.fromkeys(kept + unique_terms(history[-1])))
        if hint:
            kept = list(dict.fromkeys(kept + tokenize(hint)))

        extra: list[str] = []
        notes = list(frame.notes)
        graph = graph or TermGraph()
        people = _is_people(kept, question)

        if people:
            for alt in ("headcount", "colaboradores", "pessoas"):
                if alt not in kept and graph.has(alt):
                    extra.append(alt)
            kept = [t for t in kept if t != "aurora"]
            notes.append("pessoas → headcount")

        if frame.kind == "quantity_period" and frame.year:
            qty = [
                t
                for t in kept
                if t not in {frame.period_token, frame.year, f"q{frame.period_n}"}
            ]
            raw = graph.expand(qty, k=8) if qty else []
            period_nb: set[str] = set()
            if frame.period_n is not None:
                period_nb |= graph.neighbor_set(f"q{frame.period_n}", k=16)
            extra.extend(t for t in raw if t in period_nb)
            alt = f"q{frame.period_n}" if frame.period_n is not None else ""
            if alt and graph.has(alt) and alt != frame.period_token:
                extra.append(alt)
                notes.append(f"incluiu {alt}")
            if (
                frame.period_token
                and frame.period_token.startswith("p")
                and graph.sense_clash(frame.period_token, qty + extra + [frame.year])
            ):
                kept = [t for t in kept if t != frame.period_token]
                notes.append(f"{frame.period_token} removido (choque de sentido)")
        elif frame.year and frame.period_n is None:
            content = [t for t in kept if t != frame.year]
            raw = graph.expand(content, k=6) if content else []
            year_nb = graph.neighbor_set(frame.year, k=12)
            extra.extend(t for t in raw if t in year_nb and t not in {"indicador", "q1", "q2", "q3", "q4"})
        elif kept and not people:
            extra.extend(graph.expand(kept, k=8))

        keywords = unique_terms(" ".join(kept + extra) if (kept or extra) else cleaned)
        keywords = [k for k in keywords if k not in frame.drop]
        search = " ".join(keywords) if keywords else cleaned
        reason = f"quadro={frame.kind}; " + "; ".join(notes) if notes else f"quadro={frame.kind}"
        return RewrittenQuery(
            original=question,
            search_query=search,
            keywords=keywords,
            reason=reason,
            frame=frame,
        )


_PEOPLE_TERMS = {
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


def _is_people(kept: list[str], question: str) -> bool:
    if any(t in _PEOPLE_TERMS for t in kept):
        return True
    n = question.lower()
    return any(stem in n for stem in ("funcion", "colabor", "pessoas", "headcount", "trabalh"))
