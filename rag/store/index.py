"""Persistência: chunks + vetores TF-IDF + BM25 reconstruído na carga."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from rag.embeddings.embedder import TfidfEmbedder
from rag.ingest.chunker import Chunk
from rag.store.bm25 import BM25Index
from rag.vocab.cooccur import TermGraph


@dataclass
class RetrievedHit:
    chunk: Chunk
    dense_score: float = 0.0
    sparse_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float | None = None


@dataclass
class IndexMeta:
    embedding_kind: str
    embedding_dim: int
    chunk_count: int
    sources: list[str] = field(default_factory=list)


class VectorStore:
    def __init__(self, embeddings: np.ndarray, chunks: list[Chunk]) -> None:
        if embeddings.ndim != 2:
            raise ValueError("embeddings deve ser uma matriz (n, dim)")
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("número de chunks e embeddings divergem")
        self.embeddings = embeddings.astype(np.float32)
        self.chunks = chunks

    def search(self, query_vec: np.ndarray, top_k: int) -> list[tuple[int, float]]:
        q = query_vec.reshape(-1).astype(np.float32)
        scores = self.embeddings @ q
        k = min(top_k, len(scores))
        if k <= 0:
            return []
        idx = np.argpartition(scores, -k)[-k:]
        idx = idx[np.argsort(scores[idx])[::-1]]
        return [(int(i), float(scores[i])) for i in idx]


class RagIndex:
    def __init__(
        self,
        chunks: list[Chunk],
        embeddings: np.ndarray,
        meta: IndexMeta,
        embedder: TfidfEmbedder,
        bm25: BM25Index | None = None,
        vocab: TermGraph | None = None,
    ) -> None:
        self.chunks = chunks
        self.embeddings = embeddings
        self.meta = meta
        self.embedder = embedder
        self.vector = VectorStore(embeddings, chunks)
        self.bm25 = bm25 or BM25Index([c.text for c in chunks])
        self.vocab = vocab if vocab is not None else TermGraph().fit([c.text for c in chunks])

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / "embeddings.npy", self.embeddings)
        (directory / "chunks.json").write_text(
            json.dumps([asdict(c) for c in self.chunks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (directory / "meta.json").write_text(
            json.dumps(asdict(self.meta), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.embedder.save(directory / "tfidf.json")
        self.vocab.save(directory / "cooccur.json")

    @classmethod
    def load(cls, directory: Path) -> RagIndex:
        embeddings = np.load(directory / "embeddings.npy")
        raw_chunks = json.loads((directory / "chunks.json").read_text(encoding="utf-8"))
        chunks = [Chunk(**item) for item in raw_chunks]
        meta = IndexMeta(**json.loads((directory / "meta.json").read_text(encoding="utf-8")))
        embedder = TfidfEmbedder.load(directory / "tfidf.json")
        vocab = TermGraph.load(directory / "cooccur.json")
        if not vocab.neighbors:
            vocab = TermGraph().fit([c.text for c in chunks])
        return cls(
            chunks=chunks,
            embeddings=embeddings,
            meta=meta,
            embedder=embedder,
            vocab=vocab,
        )
