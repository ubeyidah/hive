"""Tool execution entry point for Hive agents."""

from __future__ import annotations

from typing import Dict, Optional

from hive.config.schema import ToolConfig
from hive.tools.mcp_bridge import MCPBridge
from hive.tools.registry import ToolRegistry


class ToolExecutor:
    def __init__(self, registry: ToolRegistry, mcp_bridge: MCPBridge) -> None:
        self.registry = registry
        self.mcp_bridge = mcp_bridge

    async def run(
        self,
        agent_name: str,
        agent_tools: list[ToolConfig],
        tool_name: str,
        action: str,
        params: Dict,
    ) -> Optional[Dict]:
        allowed = self.registry.has_permission(
            agent_name, tool_name, action, agent_tools
        )
        if not allowed:
            print(
                f"Permission denied: {agent_name} cannot {action} on {tool_name}"
            )
            return None
        return await self.mcp_bridge.execute(tool_name, action, params)
