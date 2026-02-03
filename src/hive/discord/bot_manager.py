"""Discord bot manager for Hive."""

from __future__ import annotations

import asyncio
from typing import List

import discord

from hive.agent.manager import AgentManager
from hive.discord.bot import HiveBot
from hive.config.loader import load_settings
from hive.tools.scheduler import ScheduleRunner, ScheduleStore


class BotManager:
    def __init__(self, agent_manager: AgentManager) -> None:
        self.agent_manager = agent_manager
        self.bots: List[HiveBot] = []
        self.schedule_store = ScheduleStore()
        self.schedule_runner = ScheduleRunner(self.schedule_store)

    def setup(self) -> None:
        settings = load_settings()
        for agent in self.agent_manager.get_all_agents():
            intents = discord.Intents.default()
            intents.message_content = True
            bot = HiveBot(
                agent,
                schedule_store=self.schedule_store,
                guild_id=settings.guild_id,
                intents=intents,
            )
            self.bots.append(bot)

    async def start_all(self) -> None:
        print(f"Starting {len(self.bots)} bots...")
        scheduler_task = asyncio.create_task(self._run_scheduler())
        await asyncio.gather(
            scheduler_task,
            *(bot.start(token=bot.agent.config.discord.token) for bot in self.bots),
        )

    async def stop_all(self) -> None:
        self.schedule_runner.stop()
        await asyncio.gather(*(bot.close() for bot in self.bots))

    async def _run_scheduler(self) -> None:
        async def execute(job) -> None:
            agent = self.agent_manager.get_agent(job.agent_name)
            if agent is None:
                return
            response = await agent.on_message(
                job.task,
                sender="scheduler",
                respond_override=True,
                message_id=f"schedule:{job.job_id}:{job.next_run}",
                context={"channel_id": job.channel_id},
            )
            if response and job.channel_id:
                bot = self._get_bot_for_agent(job.agent_name)
                if bot and bot.is_ready():
                    channel = bot.get_channel(job.channel_id)
                    if channel:
                        try:
                            await channel.send(response)
                        except discord.DiscordException as exc:
                            print(f"Discord send failed: {exc}")

        await self.schedule_runner.run(execute)

    def _get_bot_for_agent(self, agent_name: str) -> HiveBot | None:
        for bot in self.bots:
            if bot.agent.name == agent_name:
                return bot
        return None
