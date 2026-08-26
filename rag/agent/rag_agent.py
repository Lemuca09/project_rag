"""Agente de chat RAG."""

from __future__ import annotations

from rag.agent.base import BaseAgent
from rag.agent.memory import ConversationMemory
from rag.agent.protocol import AgentResult, ToolCall
from rag.agent.tools import build_rag_tools, citations_from_hits
from rag.config import Settings
from rag.retrieval.pipeline import RetrievalPipeline, RetrievalResult
from rag.retrieval.quality import AnswerVerdict, QualityGate
from rag.store.index import RetrievedHit


_REFUSAL = (
    "Não confirmo a resposta: os trechos recuperados não sustentam com segurança "
    "o que foi perguntado. Reformule ou ingira documentos mais específicos."
)


class RagChatAgent(BaseAgent):
    name = "rag_chat"
    description = "Agente de chat que responde só com o que o RAG recuperou."

    def __init__(
        self,
        retrieval: RetrievalPipeline,
        quality: QualityGate,
        settings: Settings,
        memory: ConversationMemory | None = None,
    ) -> None:
        self.memory = memory or ConversationMemory()
        self.settings = settings
        tools = build_rag_tools(
            retrieval,
            quality,
            history_fn=self.memory.user_history,
            settings=settings,
        )
        super().__init__(tools)
        self._scratchpad: list[str] = []
        self._hits: list[RetrievedHit] = []
        self._retrieval: RetrievalResult | None = None
        self._draft = ""
        self._verdict: AnswerVerdict | None = None

    def think(self, user_text: str, scratchpad: list[str]) -> ToolCall | None:
        done = {line.split(" -> ", 1)[0] for line in scratchpad}
        if "rewrite_and_retrieve" not in done:
            return ToolCall("rewrite_and_retrieve", {"question": user_text})
        if "draft_answer" not in done:
            return ToolCall(
                "draft_answer",
                {"question": user_text, "hits": self._hits},
            )
        if "verify_answer" not in done:
            return ToolCall(
                "verify_answer",
                {
                    "question": user_text,
                    "answer": self._draft,
                    "hits": self._hits,
                },
            )
        return None

    def run(self, user_text: str) -> AgentResult:
        self.memory.add("user", user_text)
        self._scratchpad = []
        self._hits = []
        self._retrieval = None
        self._draft = ""
        self._verdict = None

        for _ in range(6):
            call = self.think(user_text, self._scratchpad)
            if call is None:
                break
            result = self.act(call)
            self.observe(result, self._scratchpad)
            if not result.ok:
                text = f"Falha na tool {call.name}: {result.error}"
                self.memory.add("assistant", text)
                return AgentResult(
                    text=text,
                    messages=list(self.memory.messages),
                    tool_trace=list(self._scratchpad),
                    quality_ok=False,
                    answer_ok=False,
                )
            self._apply(call.name, result.content)

        quality_ok = bool(self._retrieval and self._retrieval.quality.ok)
        answer_ok = bool(self._verdict and self._verdict.ok)
        if quality_ok and answer_ok:
            text = self._draft
        else:
            reasons = []
            if self._retrieval:
                reasons.extend(self._retrieval.quality.reasons)
            if self._verdict:
                reasons.extend(self._verdict.reasons)
            extra = (" Motivo: " + "; ".join(reasons[:4])) if reasons else ""
            text = _REFUSAL + extra

        self.memory.add("assistant", text)
        citations = citations_from_hits(self._hits)
        if self._retrieval:
            self._scratchpad.extend(self._retrieval.trace)
        return AgentResult(
            text=text,
            messages=list(self.memory.messages),
            tool_trace=list(self._scratchpad),
            citations=citations,
            quality_ok=quality_ok,
            answer_ok=answer_ok,
        )

    def _apply(self, tool_name: str, content: object) -> None:
        if tool_name == "rewrite_and_retrieve" and isinstance(content, RetrievalResult):
            self._retrieval = content
            self._hits = content.hits
        elif tool_name == "draft_answer" and isinstance(content, str):
            self._draft = content
        elif tool_name == "verify_answer" and isinstance(content, AnswerVerdict):
            self._verdict = content
