"""Discord bot manager for Hive."""

from __future__ import annotations

import asyncio
from typing import List

import discord

from hive.agent.manager import AgentManager
from hive.discord.bot import HiveBot


class BotManager:
    def __init__(self, agent_manager: AgentManager) -> None:
        self.agent_manager = agent_manager
        self.bots: List[HiveBot] = []

    def setup(self) -> None:
        for agent in self.agent_manager.get_all_agents():
            intents = discord.Intents.default()
            intents.message_content = True
            bot = HiveBot(agent, intents=intents)
            self.bots.append(bot)

    async def start_all(self) -> None:
        print(f"Starting {len(self.bots)} bots...")
        await asyncio.gather(
            *(bot.start(token=bot.agent.config.discord.token) for bot in self.bots)
        )

    async def stop_all(self) -> None:
        await asyncio.gather(*(bot.close() for bot in self.bots))
