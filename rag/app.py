"""Monta índice, retrieval e agente."""

from __future__ import annotations

from dataclasses import dataclass

from rag.agent.rag_agent import RagChatAgent
from rag.config import Settings, load_settings
from rag.multiagent.bus import AgentRegistry, MessageBus, default_registry
from rag.retrieval.pipeline import RetrievalPipeline
from rag.retrieval.quality import QualityGate
from rag.retrieval.query_rewriter import QueryRewriter
from rag.store.index import RagIndex


@dataclass
class App:
    settings: Settings
    index: RagIndex
    agent: RagChatAgent
    registry: AgentRegistry
    bus: MessageBus


def load_index(settings: Settings | None = None) -> RagIndex:
    settings = settings or load_settings()
    if not (settings.index_dir / "chunks.json").exists():
        raise FileNotFoundError(
            f"Índice não encontrado em {settings.index_dir}. Rode: python -m rag ingest"
        )
    return RagIndex.load(settings.index_dir)


def build_app(settings: Settings | None = None) -> App:
    settings = settings or load_settings()
    index = load_index(settings)
    rewriter = QueryRewriter()
    quality = QualityGate(
        min_score=settings.quality_min_score,
        max_redundancy=settings.max_answer_redundancy,
    )
    retrieval = RetrievalPipeline(index, settings, rewriter, quality)
    agent = RagChatAgent(retrieval, quality, settings)
    registry = default_registry(agent)
    bus = MessageBus(registry)
    return App(
        settings=settings,
        index=index,
        agent=agent,
        registry=registry,
        bus=bus,
    )
