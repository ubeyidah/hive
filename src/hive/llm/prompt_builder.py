"""Prompt building utilities for Hive agents."""

from __future__ import annotations

from typing import List, Dict

from hive.config.loader import load_soul
from hive.config.schema import AgentConfig


class PromptBuilder:
    def __init__(self, agent_config: AgentConfig, all_agents: List[AgentConfig]) -> None:
        self.agent_config = agent_config
        self.soul = load_soul(agent_config.soul_path)
        self.all_agents = all_agents

    def build_system_prompt(self) -> str:
        teammates = [
            agent for agent in self.all_agents if agent.name != self.agent_config.name
        ]
        teammate_lines = [
            f"- {agent.name}: skills={agent.skills}, tools={[tool.name for tool in agent.tools]}"
            for agent in teammates
        ]
        tools_text = ", ".join(
            f"{tool.name}({', '.join(tool.permissions)})"
            for tool in self.agent_config.tools
            if tool.enabled
        )

        rules = (
            "Rules:\n"
            "- Be collaborative, mention teammates if task needs their skill\n"
            "- Respond clearly and concisely\n"
            "- Only use tools you have permission for\n"
            "- Summarize what you did when done\n"
            "- If you cannot do something, say who can\n"
            "- If the user uses @everyone or @here, respond directly and do not delegate\n"
        )
        tool_usage = (
            "To use a tool, include this in your response:\n"
            "[TOOL: tool_name | action: read/write/send | params: key=value, "
            "key=value]\n"
            "Example:\n"
            "[TOOL: gmail | action: send | params: to=user@email.com, "
            "subject=Hello, body=Hi there]\n"
            "You can only use tools you have permission for.\n\n"
            "Scheduling:\n"
            "If the user asks to schedule a task, use the schedule tool.\n"
            "Params for schedule:\n"
            "- type=interval with interval_minutes\n"
            "- type=cron with cron (minute hour * * *)\n"
            "- task=<what to do>\n"
            "- action=list to list schedules\n"
            "- action=delete with job_id to remove a schedule\n"
            "Example:\n"
            "[TOOL: schedule | action: write | params: type=interval, "
            "interval_minutes=2, task=Check if the user is awake]"
        )

        prompt_parts = [
            self.soul.strip(),
            "You are part of a team called Hive. Teammates:",
            "\n".join(teammate_lines) if teammate_lines else "- (none)",
            rules.strip(),
            tool_usage.strip(),
            f"Your tools: {tools_text}" if tools_text else "Your tools: (none)",
        ]
        return "\n\n".join(prompt_parts).strip()

    def build_messages(
        self, conversation_history: List[Dict], new_message: str
    ) -> List[Dict]:
        system_prompt = self.build_system_prompt()
        return (
            [{"role": "system", "content": system_prompt}]
            + conversation_history
            + [{"role": "user", "content": new_message}]
        )
