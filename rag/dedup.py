"""Near-duplicata por Jaccard de termos — usado na ingestão, no retrieval e na extração."""

from __future__ import annotations

from rag.text import split_sentences, tokenize


def term_set(text: str) -> frozenset[str]:
    return frozenset(tokenize(text))


def jaccard(a: str | frozenset[str], b: str | frozenset[str]) -> float:
    left = a if isinstance(a, frozenset) else term_set(a)
    right = b if isinstance(b, frozenset) else term_set(b)
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def containment(a: str, b: str) -> float:
    """Quanto de A está contido em B (pega frase curta repetida dentro de um parágrafo)."""
    left = term_set(a)
    right = term_set(b)
    if not left:
        return 0.0
    return len(left & right) / len(left)


def is_near_duplicate(
    text: str,
    others: list[str],
    *,
    threshold: float = 0.82,
) -> bool:
    terms = term_set(text)
    if not terms:
        return True
    for other in others:
        if jaccard(terms, other) >= threshold:
            return True
        if containment(text, other) >= 0.92 and len(terms) >= 4:
            return True
    return False


def answer_redundancy(answer: str) -> float:
    """0 = frases distintas; 1 = tudo repetido."""
    spans = split_sentences(answer)
    if len(spans) < 2:
        return 0.0
    scores = []
    for i, a in enumerate(spans):
        for b in spans[i + 1 :]:
            scores.append(max(jaccard(a, b), containment(a, b)))
    return max(scores) if scores else 0.0

