"""Registro de agentes e barramento de mensagens."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag.agent.base import BaseAgent
from rag.agent.protocol import AgentResult


@dataclass
class Envelope:
    sender: str
    recipient: str
    payload: str
    meta: dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent:
        if name not in self._agents:
            raise KeyError(f"agente não registrado: {name}")
        return self._agents[name]

    def names(self) -> list[str]:
        return list(self._agents)


class MessageBus:
    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry
        self.log: list[Envelope] = []

    def send(self, envelope: Envelope) -> AgentResult:
        self.log.append(envelope)
        agent = self.registry.get(envelope.recipient)
        result = agent.run(envelope.payload)
        self.log.append(
            Envelope(
                sender=envelope.recipient,
                recipient=envelope.sender,
                payload=result.text,
                meta={"quality_ok": result.quality_ok, "answer_ok": result.answer_ok},
            )
        )
        return result


def default_registry(rag_agent: BaseAgent) -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(rag_agent)
    return registry
