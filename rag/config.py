"""Configuração — lida do ambiente / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw else default


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw else default


@dataclass(frozen=True)
class Settings:
    chunk_size: int
    chunk_overlap: int
    hybrid_dense_weight: float
    hybrid_sparse_weight: float
    rrf_k: int
    retrieve_top_k: int
    rerank_top_k: int
    quality_min_score: float
    max_retrieval_retries: int
    dedup_jaccard: float
    mmr_lambda: float
    max_answer_redundancy: float
    documents_dir: Path
    index_dir: Path


def load_settings() -> Settings:
    documents = Path(os.getenv("DOCUMENTS_DIR", "data/documents"))
    index = Path(os.getenv("INDEX_DIR", "data/index"))
    if not documents.is_absolute():
        documents = ROOT / documents
    if not index.is_absolute():
        index = ROOT / index
    return Settings(
        chunk_size=_int("CHUNK_SIZE", 800),
        chunk_overlap=_int("CHUNK_OVERLAP", 120),
        hybrid_dense_weight=_float("HYBRID_DENSE_WEIGHT", 0.5),
        hybrid_sparse_weight=_float("HYBRID_SPARSE_WEIGHT", 0.5),
        rrf_k=_int("RRF_K", 60),
        retrieve_top_k=_int("RETRIEVE_TOP_K", 20),
        rerank_top_k=_int("RERANK_TOP_K", 6),
        quality_min_score=_float("QUALITY_MIN_SCORE", 0.55),
        max_retrieval_retries=_int("MAX_RETRIEVAL_RETRIES", 2),
        dedup_jaccard=_float("DEDUP_JACCARD", 0.82),
        mmr_lambda=_float("MMR_LAMBDA", 0.7),
        max_answer_redundancy=_float("MAX_ANSWER_REDUNDANCY", 0.82),
        documents_dir=documents,
        index_dir=index,
    )
