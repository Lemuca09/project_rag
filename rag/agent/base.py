"""Loop think → act → observe."""

from __future__ import annotations

from typing import Any

from rag.agent.protocol import AgentResult, ToolCall, ToolResult, ToolSpec


class BaseAgent:
    name = "base"
    description = "agente genérico"

    def __init__(self, tools: list[ToolSpec] | None = None) -> None:
        self.tools: dict[str, ToolSpec] = {t.name: t for t in (tools or [])}

    def register_tool(self, spec: ToolSpec) -> None:
        self.tools[spec.name] = spec

    def think(self, user_text: str, scratchpad: list[str]) -> ToolCall | None:
        """Decide a próxima ação. Subclasses implementam a política."""
        raise NotImplementedError

    def act(self, call: ToolCall) -> ToolResult:
        spec = self.tools.get(call.name)
        if spec is None:
            return ToolResult(name=call.name, content=None, ok=False, error="tool desconhecida")
        try:
            content = spec.handler(**call.arguments)
            return ToolResult(name=call.name, content=content, ok=True)
        except Exception as exc:
            return ToolResult(name=call.name, content=None, ok=False, error=str(exc))

    def observe(self, result: ToolResult, scratchpad: list[str]) -> None:
        status = "ok" if result.ok else f"erro:{result.error}"
        scratchpad.append(f"{result.name} -> {status}")

    def run(self, user_text: str) -> AgentResult:
        raise NotImplementedError

    def tool_schemas(self) -> list[dict[str, Any]]:
        """Lista no formato que o MCP espera (name/description/inputSchema)."""
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "inputSchema": spec.input_schema,
            }
            for spec in self.tools.values()
        ]
