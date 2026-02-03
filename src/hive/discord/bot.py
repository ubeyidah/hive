"""Discord bot implementation for Hive agents."""

from __future__ import annotations

import discord
from discord import app_commands
from typing import Optional

from hive.agent.agent import Agent
from hive.tools.scheduler import ScheduleStore


class HiveBot(discord.Client):
    def __init__(
        self,
        agent: Agent,
        schedule_store: ScheduleStore,
        guild_id: Optional[int] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.agent = agent
        self._reacted_message_ids: set[int] = set()
        self.schedule_store = schedule_store
        self.guild_id = guild_id
        self.tree = app_commands.CommandTree(self)
        self._register_commands()

    def _register_commands(self) -> None:
        hive_group = app_commands.Group(name="hive", description="Hive commands")
        schedule_group = app_commands.Group(
            name="schedule", description="Schedule tasks"
        )

        @schedule_group.command(name="add", description="Add a scheduled task")
        @app_commands.describe(
            schedule_type="interval or cron",
            task="What the agent should do",
            interval_minutes="Minutes between runs (for interval)",
            cron="Cron expression: minute hour * * * (for cron)",
        )
        async def schedule_add(
            interaction: discord.Interaction,
            schedule_type: str,
            task: str,
            interval_minutes: Optional[int] = None,
            cron: Optional[str] = None,
        ) -> None:
            schedule_type = schedule_type.lower().strip()
            if schedule_type == "interval" and not interval_minutes:
                await interaction.response.send_message(
                    "Interval schedules require interval_minutes.", ephemeral=True
                )
                return
            if schedule_type == "cron" and not cron:
                await interaction.response.send_message(
                    "Cron schedules require a cron expression.", ephemeral=True
                )
                return
            if schedule_type not in {"interval", "cron"}:
                await interaction.response.send_message(
                    "schedule_type must be 'interval' or 'cron'.", ephemeral=True
                )
                return
            job = self.schedule_store.add_job(
                agent_name=self.agent.name,
                task=task,
                schedule_type=schedule_type,
                interval_minutes=interval_minutes,
                cron=cron,
                channel_id=interaction.channel_id,
            )
            await interaction.response.send_message(
                f"Scheduled `{job.job_id}` for {self.agent.name}. Next run: {job.next_run}"
            )

        @schedule_group.command(name="list", description="List scheduled tasks")
        async def schedule_list(interaction: discord.Interaction) -> None:
            jobs = self.schedule_store.list_jobs(agent_name=self.agent.name)
            if not jobs:
                await interaction.response.send_message(
                    "No schedules for this agent.", ephemeral=True
                )
                return
            lines = [
                f"- {job.job_id} | {job.schedule_type} | next: {job.next_run} | {job.task}"
                for job in jobs
            ]
            await interaction.response.send_message("\n".join(lines))

        @schedule_group.command(name="remove", description="Remove a scheduled task")
        @app_commands.describe(job_id="Job id to remove")
        async def schedule_remove(
            interaction: discord.Interaction, job_id: str
        ) -> None:
            removed = self.schedule_store.remove_job(
                job_id, agent_name=self.agent.name
            )
            if not removed:
                await interaction.response.send_message(
                    "Job not found.", ephemeral=True
                )
                return
            await interaction.response.send_message(f"Removed schedule `{job_id}`.")

        hive_group.add_command(schedule_group)
        self.tree.add_command(hive_group)

    async def setup_hook(self) -> None:
        if self.guild_id:
            await self.tree.sync(guild=discord.Object(id=self.guild_id))
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"Bot {self.agent.name} is online")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if not message.guild:
            return

        sender = message.author.name if message.author.bot else "user"
        self.agent.shared_context.add_message(
            "user",
            message.content,
            sender,
            message_id=str(message.id),
        )
        content = message.content
        broadcast = message.mention_everyone
        mentioned_users = message.mentions or []
        mentioned_self = any(
            self.user is not None and user.id == self.user.id
            for user in mentioned_users
        )

        if mentioned_users and not mentioned_self:
            return

        if broadcast or mentioned_self:
            async with message.channel.typing():
                response = await self.agent.on_message(
                    content,
                    sender,
                    respond_override=True,
                    record_incoming=False,
                    message_id=str(message.id),
                    context={"channel_id": message.channel.id},
                )
        else:
            should_respond = await self.agent.should_respond(content)
            if not should_respond:
                return
            async with message.channel.typing():
                response = await self.agent.on_message(
                    content,
                    sender,
                    respond_override=True,
                    record_incoming=False,
                    message_id=str(message.id),
                    context={"channel_id": message.channel.id},
                )
        if response is not None:
            if response.startswith("[REACTION:"):
                reaction = response.removeprefix("[REACTION:").removesuffix("]").strip()
                try:
                    await message.add_reaction(reaction)
                except discord.DiscordException as exc:
                    print(f"Discord reaction failed: {exc}")
                return
            if "[Tool Result:" in response:
                main_response, tool_block = response.split("[Tool Result:", 1)
                main_response = main_response.strip()
                tool_block = "[Tool Result:" + tool_block
                if main_response:
                    try:
                        await message.channel.send(main_response)
                    except discord.DiscordException as exc:
                        print(f"Discord send failed: {exc}")
                        return
                try:
                    await message.channel.send(f"```{tool_block.strip()}```")
                    await message.add_reaction("✅")
                except discord.DiscordException as exc:
                    print(f"Discord send failed: {exc}")
            else:
                try:
                    await message.channel.send(response)
                except discord.DiscordException as exc:
                    print(f"Discord send failed: {exc}")

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        if user.bot:
            return
        if self.user is None:
            return
        if reaction.message.author.id != self.user.id:
            return
        if reaction.message.id in self._reacted_message_ids:
            return

        reply_text, react_emoji = await self.agent.handle_reaction(
            str(reaction.emoji),
            reaction.message.content or "",
            user.display_name,
        )
        if react_emoji:
            try:
                await reaction.message.add_reaction(react_emoji)
            except discord.DiscordException as exc:
                print(f"Discord reaction failed: {exc}")
        if reply_text:
            try:
                await reaction.message.channel.send(reply_text)
            except discord.DiscordException as exc:
                print(f"Discord send failed: {exc}")
        if react_emoji or reply_text:
            self._reacted_message_ids.add(reaction.message.id)
