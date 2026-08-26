"""Ingestão: arquivos → chunks → vetores TF-IDF → índice persistido."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag.config import Settings
from rag.embeddings.embedder import TfidfEmbedder
from rag.ingest.chunker import Chunk, chunk_documents
from rag.ingest.dedup import dedupe_chunks
from rag.ingest.loader import load_path
from rag.store.index import IndexMeta, RagIndex


@dataclass
class IngestResult:
    documents: int
    chunks: int
    dropped_duplicates: int
    index_dir: Path
    sources: list[str]


def ingest(
    source: Path,
    settings: Settings,
    *,
    embedder: TfidfEmbedder | None = None,
) -> IngestResult:
    documents = load_path(source)
    if not documents:
        raise ValueError(f"Nenhum arquivo suportado em {source}")
    chunks: list[Chunk] = chunk_documents(
        documents,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )
    chunks, dropped = dedupe_chunks(chunks, threshold=settings.dedup_jaccard)
    if not chunks:
        raise ValueError("Todos os chunks foram descartados como vazios ou duplicados")
    model = embedder or TfidfEmbedder()
    embeddings = model.fit_transform([c.text for c in chunks])
    sources = sorted({c.source for c in chunks})
    index = RagIndex(
        chunks=chunks,
        embeddings=embeddings,
        embedder=model,
        meta=IndexMeta(
            embedding_kind="tfidf",
            embedding_dim=int(embeddings.shape[1]),
            chunk_count=len(chunks),
            sources=sources,
        ),
    )
    index.save(settings.index_dir)
    return IngestResult(
        documents=len(documents),
        chunks=len(chunks),
        dropped_duplicates=dropped,
        index_dir=settings.index_dir,
        sources=sources,
    )
