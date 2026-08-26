"""Serializa tools no formato MCP."""

from __future__ import annotations

from typing import Any

from rag.agent.base import BaseAgent
from rag.agent.protocol import ToolSpec


def tools_to_mcp(tools: list[ToolSpec] | BaseAgent) -> list[dict[str, Any]]:
    """Converte ToolSpec para o schema MCP."""
    specs = tools.tools.values() if isinstance(tools, BaseAgent) else tools
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "inputSchema": spec.input_schema,
        }
        for spec in specs
    ]


def dispatch_mcp_call(agent: BaseAgent, name: str, arguments: dict[str, Any]) -> Any:
    """Despacha a tool pelo nome."""
    spec = agent.tools.get(name)
    if spec is None:
        raise KeyError(f"tool MCP desconhecida: {name}")
    return spec.handler(**arguments)
