"""Agent brain implementation for Hive."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from hive.agent.context import SharedContext
from hive.config.schema import AgentConfig, LLMConfig
from hive.llm.client import HiveLLMClient
from hive.llm.prompt_builder import PromptBuilder
from hive.tools.executor import ToolExecutor


class Agent:
    def __init__(
        self,
        config: AgentConfig,
        all_agents: List[AgentConfig],
        shared_context: SharedContext,
        llm_config: LLMConfig,
        tool_executor: ToolExecutor,
    ) -> None:
        self.config = config
        self.llm_client = HiveLLMClient(llm_config)
        self.prompt_builder = PromptBuilder(config, all_agents)
        self.shared_context = shared_context
        self.tool_executor = tool_executor
        self.name = config.name

    async def on_message(
        self,
        message: str,
        sender: str,
        respond_override: Optional[bool] = None,
        record_incoming: bool = True,
        message_id: Optional[str] = None,
    ) -> Optional[str]:
        if record_incoming:
            self.shared_context.add_message(
                "user", message, sender, message_id=message_id
            )

        if sender == self.name:
            return None

        if respond_override is None:
            should_respond = False
            if f"@{self.name}" in message:
                should_respond = True
            else:
                should_respond = await self.should_respond(message)
        else:
            should_respond = respond_override

        if not should_respond:
            reaction = await self._decide_reaction_to_message(message, sender)
            if reaction:
                return f"[REACTION: {reaction}]"
            return None

        messages = self.prompt_builder.build_messages(
            self.shared_context.get_history_for_llm(), message
        )
        response = await self.llm_client.chat(messages)
        if response is None:
            return None

        tool_call = self._parse_tool_call(response)
        if tool_call:
            result = await self.tool_executor.run(
                self.name,
                self.config.tools,
                tool_call["tool_name"],
                tool_call["action"],
                tool_call["params"],
            )
            if result is not None:
                response = (
                    f"{response}\n\n[Tool Result: {tool_call['tool_name']}]\n{result}"
                )

        self.shared_context.add_message("assistant", response, self.name)
        return response

    async def handle_reaction(
        self, reaction: str, message_content: str, reactor: str
    ) -> Tuple[Optional[str], Optional[str]]:
        prompt = (
            "A user reacted to your message.\n"
            f"Reaction: {reaction}\n"
            f"User: {reactor}\n"
            f"Message: {message_content}\n\n"
            "Decide if you should reply or react back.\n"
            "Reply should be short if provided.\n"
            "Return two lines exactly:\n"
            "REPLY: <text or NONE>\n"
            "REACT: <emoji or NONE>"
        )
        response = await self.llm_client.chat([{"role": "user", "content": prompt}])
        if not response:
            return None, None

        reply_text: Optional[str] = None
        react_emoji: Optional[str] = None
        for line in response.splitlines():
            if line.upper().startswith("REPLY:"):
                value = line.split(":", 1)[1].strip()
                if value.upper() != "NONE" and value:
                    reply_text = value
            if line.upper().startswith("REACT:"):
                value = line.split(":", 1)[1].strip()
                if value.upper() != "NONE" and value:
                    react_emoji = value
        return reply_text, react_emoji

    async def should_respond(self, message: str) -> bool:
        soul_lines = [line for line in self.prompt_builder.soul.splitlines() if line]
        soul_summary = soul_lines[0] if soul_lines else "Hive agent"
        prompt = (
            "Given this message: '{message}'\n"
            "And your role: {soul_summary}\n"
            "Should you respond? Answer only: YES or NO"
        ).format(message=message, soul_summary=soul_summary)
        response = await self.llm_client.chat(
            [{"role": "user", "content": prompt}]
        )
        if response and "YES" in response.upper():
            return True
        return False

    def _parse_tool_call(self, response: str) -> Optional[Dict[str, object]]:
        match = re.search(
            r"\[TOOL:\s*(?P<tool>[^|]+)\s*\|\s*action:\s*(?P<action>[^|]+)"
            r"\s*\|\s*params:\s*(?P<params>[^\]]+)\]",
            response,
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        tool_name = match.group("tool").strip()
        action = match.group("action").strip().lower()
        params = self._parse_params(match.group("params"))
        return {"tool_name": tool_name, "action": action, "params": params}

    @staticmethod
    def _parse_params(raw_params: str) -> Dict[str, str]:
        params: Dict[str, str] = {}
        for item in raw_params.split(","):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key:
                params[key] = value
        return params

    async def _decide_reaction_to_message(
        self, message: str, sender: str
    ) -> Optional[str]:
        prompt = (
            "Decide if you should react (emoji only) to this message instead of "
            "replying.\n"
            f"User: {sender}\n"
            f"Message: {message}\n\n"
            "If a reaction is appropriate, respond with a single emoji only.\n"
            "If no reaction, respond with NONE."
        )
        response = await self.llm_client.chat([{"role": "user", "content": prompt}])
        if not response:
            return None
        cleaned = response.strip()
        if cleaned.upper().startswith("NONE"):
            return None
        first_line = cleaned.splitlines()[0].strip()
        first_token = first_line.split(" ")[0].strip()
        return first_token if first_token else None
