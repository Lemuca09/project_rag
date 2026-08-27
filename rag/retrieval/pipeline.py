"""Pipeline de retrieval usado pelo agente: rewrite → hybrid → rerank → quality."""

from __future__ import annotations

from dataclasses import dataclass, field

from rag.config import Settings
from rag.retrieval.hybrid import hybrid_search
from rag.retrieval.quality import QualityGate, QualityReport
from rag.retrieval.query_rewriter import QueryRewriter, RewrittenQuery
from rag.retrieval.reranker import rerank
from rag.retrieval.route import scan_latest_year
from rag.store.index import RagIndex, RetrievedHit


@dataclass
class RetrievalResult:
    rewritten: RewrittenQuery
    hits: list[RetrievedHit]
    quality: QualityReport
    attempts: int
    trace: list[str] = field(default_factory=list)


class RetrievalPipeline:
    def __init__(
        self,
        index: RagIndex,
        settings: Settings,
        rewriter: QueryRewriter,
        quality: QualityGate,
    ) -> None:
        self.index = index
        self.settings = settings
        self.rewriter = rewriter
        self.quality = quality
        self._latest_year: str | None = None
        self._scanned = False
        self._last_keywords: list[str] = []

    def _corpus_signals(self) -> tuple[str | None, list[str]]:
        if not self._scanned:
            self._latest_year = scan_latest_year(self.index.chunks)
            self._scanned = True
        return self._latest_year, self._last_keywords

    def retrieve(
        self,
        question: str,
        *,
        history: list[str] | None = None,
    ) -> RetrievalResult:
        hint: str | None = None
        rewritten = self.rewriter.rewrite(question, history=history, graph=self.index.vocab)
        hits: list[RetrievedHit] = []
        quality = QualityReport(ok=False, score=0.0)
        trace: list[str] = []
        attempts = 0

        for attempt in range(self.settings.max_retrieval_retries + 1):
            attempts = attempt + 1
            rewritten = self.rewriter.rewrite(
                question,
                history=history,
                hint=hint,
                graph=self.index.vocab,
            )
            trace.append(
                f"tentativa {attempts}: query='{rewritten.search_query}' ({rewritten.reason})"
            )
            hits = hybrid_search(self.index, rewritten.search_query, self.settings)
            latest_year, _ = self._corpus_signals()
            hits = rerank(
                rewritten.search_query,
                hits,
                top_k=self.settings.rerank_top_k,
                mmr_lambda=self.settings.mmr_lambda,
                frame=rewritten.frame,
                route_query=question,
                latest_year=latest_year,
                graph=self.index.vocab,
            )
            self._last_keywords = rewritten.keywords
            quality = self.quality.evaluate_retrieval(
                rewritten.original, hits, graph=self.index.vocab
            )
            trace.append(
                f"qualidade={quality.score:.2f} ok={quality.ok} | " + "; ".join(quality.reasons)
            )
            if quality.ok:
                break
            hint = quality.hint or " ".join(quality.missing_terms)

        return RetrievalResult(
            rewritten=rewritten,
            hits=hits,
            quality=quality,
            attempts=attempts,
            trace=trace,
        )
