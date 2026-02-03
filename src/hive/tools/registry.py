"""Tool registry and permissions for Hive."""

from __future__ import annotations

from typing import Dict, List, Optional

from hive.config.schema import ToolConfig


class ToolRegistry:
    def __init__(self) -> None:
        self.tools: Dict[str, ToolConfig] = {}

    def register(self, tool_config: ToolConfig) -> None:
        self.tools[tool_config.name] = tool_config

    def get_tool(self, name: str) -> Optional[ToolConfig]:
        return self.tools.get(name)

    def has_permission(
        self,
        agent_name: str,
        tool_name: str,
        action: str,
        agent_tools: List[ToolConfig],
    ) -> bool:
        tool = next((item for item in agent_tools if item.name == tool_name), None)
        if tool is None or not tool.enabled:
            return False
        return action in tool.permissions

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())
