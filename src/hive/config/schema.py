"""Dataclass schemas for Hive configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str


@dataclass
class DiscordConfig:
    token: str
    guild_id: int


@dataclass
class ToolConfig:
    name: str
    enabled: bool
    mcp_server_url: Optional[str]
    permissions: List[str]


@dataclass
class AgentConfig:
    name: str
    soul_path: str
    skills: List[str]
    tools: List[ToolConfig]
    discord: DiscordConfig
    llm: LLMConfig


@dataclass
class HiveSettings:
    default_llm: LLMConfig
    guild_id: int
