"""Agent manager for Hive."""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Tuple

from hive.agent.agent import Agent
from hive.agent.context import SharedContext
from hive.config.loader import load_all_agents, load_settings
from hive.tools.executor import ToolExecutor
from hive.tools.mcp_bridge import MCPBridge
from hive.tools.registry import ToolRegistry
from hive.tools.scheduler import ScheduleStore


class AgentManager:
    def __init__(self) -> None:
        self.agents: Dict[str, Agent] = {}
        self.shared_context = SharedContext()

    def setup(self) -> None:
        settings = load_settings()
        agent_configs = load_all_agents()
        registry = ToolRegistry()
        schedule_store = ScheduleStore()
        for config in agent_configs:
            for tool in config.tools:
                if registry.get_tool(tool.name) is None:
                    registry.register(tool)
        mcp_bridge = MCPBridge(registry)
        tool_executor = ToolExecutor(registry, mcp_bridge, schedule_store)
        for config in agent_configs:
            llm_config = config.llm or settings.default_llm
            agent = Agent(
                config, agent_configs, self.shared_context, llm_config, tool_executor
            )
            self.agents[config.name] = agent

    def get_agent(self, name: str) -> Optional[Agent]:
        return self.agents.get(name)

    def get_all_agents(self) -> List[Agent]:
        return list(self.agents.values())

    async def route_message(self, message: str, sender: str) -> List[Tuple[str, str]]:
        tasks = [agent.on_message(message, sender) for agent in self.agents.values()]
        results = await asyncio.gather(*tasks)
        responses: List[Tuple[str, str]] = []
        for agent, result in zip(self.agents.values(), results):
            if result is not None:
                responses.append((agent.name, result))
        return responses
