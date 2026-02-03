"""Discord bot implementation for Hive agents."""

from __future__ import annotations

import discord

from hive.agent.agent import Agent


class HiveBot(discord.Client):
    def __init__(self, agent: Agent, **kwargs) -> None:
        super().__init__(**kwargs)
        self.agent = agent
        self._reacted_message_ids: set[int] = set()

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
