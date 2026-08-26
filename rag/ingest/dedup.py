"""Remove chunks repetidos ou quase iguais entre documentos internos."""

from __future__ import annotations

from rag.dedup import is_near_duplicate, term_set
from rag.ingest.chunker import Chunk


def dedupe_chunks(chunks: list[Chunk], *, threshold: float = 0.82) -> tuple[list[Chunk], int]:
    kept: list[Chunk] = []
    seen_keys: set[frozenset[str]] = set()
    seen_facts: set[tuple[str, str, str]] = set()
    dropped = 0
    for chunk in chunks:
        key = term_set(chunk.text)
        if not key:
            dropped += 1
            continue
        if key in seen_keys:
            dropped += 1
            continue
        if chunk.metadata.get("kind") == "table_fact":
            fact_key = (
                chunk.metadata.get("source_name", chunk.source),
                chunk.metadata.get("metric", ""),
                chunk.metadata.get("period", ""),
            )
            if fact_key in seen_facts:
                dropped += 1
                continue
            seen_facts.add(fact_key)
            seen_keys.add(key)
            kept.append(chunk)
            continue
        if is_near_duplicate(chunk.text, [c.text for c in kept], threshold=threshold):
            dropped += 1
            continue
        seen_keys.add(key)
        kept.append(chunk)
    return kept, dropped
