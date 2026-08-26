"""Chunking por seção Markdown; tabelas viram fatos por linha/célula (período)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from rag.ingest.loader import Document
from rag.ingest.tables import explode_table, split_prose_and_tables

_HEADING = re.compile(r"^(#{1,6})\s+\S")


@dataclass
class Chunk:
    chunk_id: str
    source: str
    text: str
    index: int
    metadata: dict = field(default_factory=dict)


def chunk_documents(
    documents: list[Document],
    *,
    chunk_size: int = 800,
    overlap: int = 80,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in documents:
        source_name = Path(doc.source).name
        sections = split_sections(doc.text)
        local_index = 0
        for heading, body in sections:
            pieces = _chunk_section(heading, body, chunk_size=chunk_size, overlap=overlap)
            for piece in pieces:
                text = piece["text"]
                chunks.append(
                    Chunk(
                        chunk_id=f"{source_name}::{local_index}",
                        source=doc.source,
                        text=text,
                        index=local_index,
                        metadata={
                            **doc.metadata,
                            "source_name": source_name,
                            "section": heading.lstrip("# ").strip() if heading else "",
                            "kind": piece.get("kind", "prose"),
                            "period": piece.get("period", ""),
                            "metric": piece.get("metric", ""),
                        },
                    )
                )
                local_index += 1
    return chunks


def split_sections(text: str) -> list[tuple[str, str]]:
    lines = text.replace("\r\n", "\n").split("\n")
    sections: list[tuple[str, list[str]]] = []
    heading = ""
    buf: list[str] = []
    for line in lines:
        if _HEADING.match(line.strip()):
            if buf or heading:
                sections.append((heading, buf))
            heading = line.strip()
            buf = []
        else:
            buf.append(line)
    if buf or heading:
        sections.append((heading, buf))
    result: list[tuple[str, str]] = []
    for head, body_lines in sections:
        body = "\n".join(body_lines).strip()
        if body:
            result.append((head, body))
        elif head:
            result.append((head, head.lstrip("# ").strip()))
    return result or [("", text.strip())]


def _chunk_section(
    heading: str,
    body: str,
    *,
    chunk_size: int,
    overlap: int,
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for kind, block in split_prose_and_tables(body):
        if kind == "table":
            facts = explode_table(block, heading=heading)
            if facts:
                out.extend(facts)
                continue
        prefix = f"{heading}\n\n" if heading else ""
        for window in split_text(block, chunk_size=chunk_size, overlap=overlap):
            out.append({"text": f"{prefix}{window}".strip(), "kind": "prose"})
    return out


def split_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]
    parts: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        window = cleaned[start:end]
        if end < len(cleaned):
            cut = max(
                window.rfind("\n\n"),
                window.rfind(". "),
                window.rfind("? "),
                window.rfind("! "),
            )
            if cut >= chunk_size // 4:
                window = window[: cut + 1]
                end = start + cut + 1
        parts.append(window.strip())
        if end >= len(cleaned):
            break
        start += max(end - start - overlap, 1)
        if start <= 0:
            start = end
    return [p for p in parts if p]
