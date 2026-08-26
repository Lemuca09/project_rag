"""Histórico da conversa."""

from __future__ import annotations

from rag.agent.protocol import Message


class ConversationMemory:
    def __init__(self, max_turns: int = 20) -> None:
        self.max_turns = max_turns
        self.messages: list[Message] = []

    def add(self, role: str, content: str, **meta: object) -> Message:
        msg = Message(role=role, content=content, meta=dict(meta))
        self.messages.append(msg)
        overflow = len(self.messages) - self.max_turns * 2
        if overflow > 0:
            self.messages = self.messages[overflow:]
        return msg

    def user_history(self) -> list[str]:
        return [m.content for m in self.messages if m.role == "user"]

    def as_dicts(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]
