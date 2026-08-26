"""Tools do agente RAG."""

from __future__ import annotations

from typing import Any, Callable

from rag.agent.extract import extract_answer
from rag.agent.protocol import ToolSpec
from rag.config import Settings
from rag.retrieval.pipeline import RetrievalPipeline, RetrievalResult
from rag.retrieval.quality import AnswerVerdict, QualityGate
from rag.store.index import RetrievedHit


def build_rag_tools(
    retrieval: RetrievalPipeline,
    quality: QualityGate,
    history_fn: Callable[[], list[str]],
    settings: Settings,
) -> list[ToolSpec]:
    def rewrite_and_retrieve(question: str) -> RetrievalResult:
        return retrieval.retrieve(question, history=history_fn())

    def draft_answer(question: str, hits: list[RetrievedHit]) -> str:
        return extract_answer(
            question,
            hits,
            mmr_lambda=settings.mmr_lambda,
            dup_threshold=settings.dedup_jaccard,
        )

    def verify(question: str, answer: str, hits: list[RetrievedHit]) -> AnswerVerdict:
        return quality.verify_answer(question, answer, hits)

    return [
        ToolSpec(
            name="rewrite_and_retrieve",
            description=(
                "Reescreve a pergunta, busca híbrida no índice, faz rerank "
                "e avalia a qualidade dos trechos."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Pergunta do usuário"}
                },
                "required": ["question"],
            },
            handler=rewrite_and_retrieve,
        ),
        ToolSpec(
            name="draft_answer",
            description="Monta a resposta só com frases dos trechos recuperados.",
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "hits": {"type": "array"},
                },
                "required": ["question", "hits"],
            },
            handler=draft_answer,
        ),
        ToolSpec(
            name="verify_answer",
            description="Confere se a resposta está apoiada nos trechos antes de entregar.",
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                    "hits": {"type": "array"},
                },
                "required": ["question", "answer", "hits"],
            },
            handler=verify,
        ),
    ]


def citations_from_hits(hits: list[RetrievedHit]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for hit in hits:
        items.append(
            {
                "chunk_id": hit.chunk.chunk_id,
                "source": hit.chunk.metadata.get("source_name", hit.chunk.source),
                "rerank": hit.rerank_score,
                "preview": hit.chunk.text[:180],
            }
        )
    return items
