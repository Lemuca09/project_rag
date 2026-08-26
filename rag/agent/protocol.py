"""Contrato do agente e das tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass
class Message:
    role: str
    content: str
    name: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Any]


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    name: str
    content: Any
    ok: bool = True
    error: str | None = None


@dataclass
class AgentResult:
    text: str
    messages: list[Message]
    tool_trace: list[str]
    citations: list[dict[str, Any]] = field(default_factory=list)
    quality_ok: bool = False
    answer_ok: bool = False


class Agent(Protocol):
    name: str
    description: str

    def run(self, user_text: str) -> AgentResult: ...
