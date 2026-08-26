"""Classifica o tipo da pergunta (quantidade, período, definição)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rag.text import normalize


_DEFINITION = re.compile(
    r"\b(do que se trata|o que (e|eh|é)|quem (e|eh|é)|o que faz)\b",
    re.IGNORECASE,
)
_QUANTITY = re.compile(
    r"\b(quanto|quantos|quantas|ganh\w*|fatur\w*|receita|valor|lucro)\b",
    re.IGNORECASE,
)
_PEOPLE = re.compile(
    r"\b(funcionari\w*|colaborador\w*|pessoas|pessoa|headcount|"
    r"trabalh\w+|quadro de pessoal)\b",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\b(20\d{2})\b")
_PERIOD = re.compile(
    r"\b(?:na|no|em)?\s*([pq])\s*([1-4])(?:\s+de)?\s+(20\d{2})\b",
    re.IGNORECASE,
)
_INCIDENT_ID = re.compile(r"\bp1-\d{4}-\d+\b", re.IGNORECASE)
_INCIDENT_WORD = re.compile(r"\b(incidente|severidade|postmortem|ack)\b", re.IGNORECASE)

_LIGHT = {"trata", "tratar", "sobre", "ser", "fazer"}


@dataclass
class QuestionFrame:
    kind: str
    period_n: int | None = None
    year: str | None = None
    period_token: str | None = None
    drop: tuple[str, ...] = ()
    notes: list[str] = field(default_factory=list)


def parse_frame(question: str) -> QuestionFrame:
    n = normalize(question)
    n = n.replace('"', " ").replace("'", " ").replace("“", " ").replace("”", " ")
    if _INCIDENT_ID.search(n) or _INCIDENT_WORD.search(n):
        return QuestionFrame(kind="incident", notes=["quadro de incidente explícito"])
    period = _PERIOD.search(n)
    year_m = _YEAR.search(n)
    year = year_m.group(1) if year_m else None
    quantity = bool(_QUANTITY.search(n) or _QUANTITY.search(question))
    people = bool(_PEOPLE.search(n) or _PEOPLE.search(question))
    if period and (quantity or people):
        letter, digit, pyear = period.group(1), int(period.group(2)), period.group(3)
        token = f"{letter}{digit}"
        return QuestionFrame(
            kind="quantity_period",
            period_n=digit,
            year=pyear or year,
            period_token=token,
            drop=_LIGHT,
            notes=[f"quantidade + período {token} {pyear}"],
        )
    if people or quantity:
        return QuestionFrame(
            kind="quantity",
            year=year,
            drop=_LIGHT,
            notes=["quadro de quantidade" + (" de pessoas" if people else "")],
        )
    if _DEFINITION.search(question) or _DEFINITION.search(n):
        return QuestionFrame(
            kind="definition",
            year=year,
            drop=_LIGHT,
            notes=["definição"],
        )
    if year:
        return QuestionFrame(
            kind="generic",
            year=year,
            drop=_LIGHT,
            notes=[f"ano explícito ({year})"],
        )
    return QuestionFrame(kind="generic")
