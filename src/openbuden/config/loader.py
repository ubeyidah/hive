"""YAML configuration loader for Openbuden."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv

from .schema import AgentConfig, DiscordConfig, OpenbudenSettings, LLMConfig, ToolConfig


CONFIG_DIRNAME = ".config/openbuden"
API_KEY_ENV = "OPENBUDEN_LLM_API_KEY"


def get_config_dir() -> Path:
    """Return the Openbuden config directory, creating it if needed."""
    config_dir = Path.home() / CONFIG_DIRNAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_settings() -> OpenbudenSettings:
    """Load the global Openbuden settings."""
    load_dotenv()
    settings_path = get_config_dir() / "settings.yaml"
    if not settings_path.exists():
        raise FileNotFoundError("Settings not found. Run 'openbuden config' to set up.")

    data = _read_yaml_dict(settings_path)
    default_llm_data = _require_mapping(data, "default_llm", settings_path)
    default_llm = _parse_llm_config(default_llm_data, settings_path)
    guild_id = _require_int(data, "guild_id", settings_path)

    return OpenbudenSettings(
        default_llm=default_llm,
        guild_id=guild_id,
    )


def load_agent(agent_name: str) -> AgentConfig:
    """Load a single agent configuration by name."""
    agent_dir = get_config_dir() / "agents" / agent_name
    if not agent_dir.exists() or not agent_dir.is_dir():
        raise FileNotFoundError(f"Agent '{agent_name}' not found.")

    settings = load_settings()
    agent_path = agent_dir / "agent.yaml"
    skills_path = agent_dir / "skills.yaml"
    tools_path = agent_dir / "tools.yaml"
    soul_path = agent_dir / "soul.md"

    agent_data = _read_yaml_dict(agent_path)
    skills = _read_yaml_list(skills_path)
    tools_data = _read_yaml_list(tools_path)
    tools = [_parse_tool_config(item) for item in tools_data]

    if not soul_path.exists():
        raise FileNotFoundError(f"Soul file not found: {soul_path}")

    name = _require_str(agent_data, "name", agent_path)
    discord_data = _require_mapping(agent_data, "discord", agent_path)
    token = _require_str(discord_data, "token", agent_path)

    llm_data = agent_data.get("llm")
    if llm_data is None:
        llm = settings.default_llm
    elif isinstance(llm_data, dict):
        llm = _parse_llm_config(llm_data, agent_path)
    else:
        raise ValueError(f"Invalid LLM config in {agent_path}")

    return AgentConfig(
        name=name,
        soul_path=str(soul_path),
        skills=[str(item) for item in skills],
        tools=tools,
        discord=DiscordConfig(token=token, guild_id=settings.guild_id),
        llm=llm,
    )


def load_all_agents() -> List[AgentConfig]:
    """Load all agents in the config directory."""
    agents_dir = get_config_dir() / "agents"
    if not agents_dir.exists():
        return []

    agents: List[AgentConfig] = []
    for entry in sorted(agents_dir.iterdir()):
        if entry.is_dir():
            agents.append(load_agent(entry.name))
    return agents


def load_soul(soul_path: str) -> str:
    """Read and return the soul markdown content."""
    path = Path(soul_path)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FileNotFoundError(f"Unable to read soul file: {path}") from exc


def _read_yaml_dict(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}")

    return data


def _read_yaml_list(path: Path) -> List[Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or []

    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {path}")

    return data


def _parse_llm_config(data: Dict[str, Any], source: Path) -> LLMConfig:
    api_key = data.get("api_key")
    if not api_key:
        api_key = _load_api_key(source)
    return LLMConfig(
        provider=_require_str(data, "provider", source),
        model=_require_str(data, "model", source),
        api_key=str(api_key),
    )


def _parse_tool_config(data: Any) -> ToolConfig:
    if not isinstance(data, dict):
        raise ValueError("Invalid tool config")
    permissions = data.get("permissions") or []
    if not isinstance(permissions, list):
        raise ValueError("Invalid tool permissions")

    return ToolConfig(
        name=_require_str(data, "name", None),
        enabled=bool(data.get("enabled")),
        mcp_server_url=data.get("mcp_server_url"),
        permissions=[str(item) for item in permissions],
    )


def _load_api_key(source: Path) -> str:
    api_key = _get_env(API_KEY_ENV)
    if not api_key:
        raise ValueError(
            f"Missing API key. Set {API_KEY_ENV} in .env (needed by {source})."
        )
    return api_key


def _get_env(key: str) -> str:
    value = __import__("os").environ.get(key)
    return value or ""


def _require_mapping(data: Dict[str, Any], key: str, source: Path) -> Dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing or invalid '{key}' in {source}")
    return value


def _require_str(data: Dict[str, Any], key: str, source: Path | None) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        location = f" in {source}" if source else ""
        raise ValueError(f"Missing or invalid '{key}'{location}")
    return value


def _require_int(data: Dict[str, Any], key: str, source: Path) -> int:
    value = data.get(key)
    if isinstance(value, bool) or value is None:
        raise ValueError(f"Missing or invalid '{key}' in {source}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Missing or invalid '{key}' in {source}") from exc
