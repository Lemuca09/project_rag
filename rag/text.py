"""Tokenização e stopwords — compartilhado por TF-IDF, BM25 e o agente."""

from __future__ import annotations

import re
import unicodedata

_TOKEN = re.compile(r"[a-z0-9áàâãéêíóôõúç]+", re.IGNORECASE)

STOPWORDS_PT = {
    "a", "ao", "aos", "as", "ate", "com", "como", "da", "das", "de", "do",
    "dos", "e", "em", "era", "eram", "essa", "esse", "esta", "este", "eu",
    "foi", "for", "isso", "isto", "ja", "la", "lhe", "lo", "mais", "mas",
    "me", "mesmo", "meu", "minha", "na", "nao", "nas", "nem", "no", "nos",
    "nossa", "o", "os", "ou", "para", "pela", "pelo", "por", "qual", "quando",
    "que", "quem", "se", "sem", "seu", "sua", "sao", "so", "também", "tambem",
    "te", "tem", "tendo", "ter", "teu", "teve", "tinha", "tive", "tu", "um",
    "uma", "uns", "umas", "voce", "voces", "vos",
}

FILLER_PT = {
    "me", "explica", "explique", "diz", "diga", "fala", "fale", "quero",
    "saber", "pode", "poderia", "gostaria", "sobre", "qual", "quais",
    "quanto", "quantos", "quantas", "onde", "como", "por", "porque",
    "pq", "o", "a", "os", "as", "de", "do", "da", "em", "no", "na",
    "que", "é", "eh", "seria", "pra", "para", "por favor", "pfv",
    "trata",
}


def normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in folded if not unicodedata.combining(ch))


def tokenize(text: str, *, drop_stopwords: bool = True) -> list[str]:
    tokens = _TOKEN.findall(normalize(text))
    if drop_stopwords:
        return [t for t in tokens if t not in STOPWORDS_PT and len(t) > 1]
    return [t for t in tokens if len(t) > 1]


def unique_terms(text: str) -> list[str]:
    seen: list[str] = []
    for token in tokenize(text):
        if token not in seen:
            seen.append(token)
    return seen


def split_sentences(text: str) -> list[str]:
    parts: list[str] = []
    for block in re.split(r"\n{2,}", text):
        block = block.strip()
        if not block or block.lstrip().startswith("#"):
            continue
        if any(ln.strip().startswith("|") for ln in block.split("\n")):
            for ln in block.split("\n"):
                s = ln.strip()
                if s.startswith("|") or not s:
                    continue
                if len(s) > 24:
                    parts.append(s)
            continue
        buf: list[str] = []
        for i, ch in enumerate(block):
            buf.append(ch)
            if ch in ".!?":
                prev = buf[-2] if len(buf) >= 2 else ""
                nxt = block[i + 1] if i + 1 < len(block) else ""
                last = "".join(buf).rstrip(".!?").split()[-1] if buf else ""
                if ch == "." and (
                    prev.isdigit() or nxt.isdigit() or (last.isalpha() and len(last) <= 4)
                ):
                    continue
                sentence = "".join(buf).strip()
                if len(sentence) > 24:
                    parts.append(sentence)
                buf = []
        tail = "".join(buf).strip()
        if len(tail) > 24:
            parts.append(tail)
    return parts or ([text.strip()] if len(text.strip()) > 24 else [])

