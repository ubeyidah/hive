"""CLI entry point for Hive."""

import asyncio
import click
import sys
from pathlib import Path

import yaml

try:
    from hive.agent.manager import AgentManager
    from hive.config.loader import get_config_dir, load_all_agents, load_settings
    from hive.discord.bot_manager import BotManager
    from hive.llm.client import HiveLLMClient
    from hive.tools.mcp_bridge import MCPBridge
    from hive.tools.registry import ToolRegistry
except ModuleNotFoundError:  # Allows `python src/hive/cli.py ...`
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from hive.agent.manager import AgentManager
    from hive.config.loader import get_config_dir, load_all_agents, load_settings
    from hive.discord.bot_manager import BotManager
    from hive.llm.client import HiveLLMClient
    from hive.tools.mcp_bridge import MCPBridge
    from hive.tools.registry import ToolRegistry


@click.group()
def main() -> None:
    """Hive command line interface."""


@main.command()
def start() -> None:
    """Start Hive services."""
    agent_manager = AgentManager()
    agent_manager.setup()
    bot_manager = BotManager(agent_manager)
    bot_manager.setup()
    try:
        asyncio.run(bot_manager.start_all())
    except KeyboardInterrupt:
        click.echo("Shutting down Hive...")
        asyncio.run(bot_manager.stop_all())


@main.command("add-agent")
def add_agent() -> None:
    """Add a new agent."""
    name = click.prompt("Agent name?", type=str)
    discord_token = click.prompt("Discord bot token?", type=str, hide_input=True)
    skills_input = click.prompt("Skills? (comma separated)", type=str)
    tools_input = click.prompt(
        "Tools? (comma separated, e.g. gmail, calendar, notion)", type=str
    )
    provider = click.prompt(
        "LLM provider? (openai, anthropic, groq) "
        "[press enter to use default from settings]",
        type=str,
        default="",
        show_default=False,
    ).strip()

    skills = [item.strip() for item in skills_input.split(",") if item.strip()]
    tools = [item.strip() for item in tools_input.split(",") if item.strip()]

    agent_dir = get_config_dir() / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)

    (agent_dir / "skills.yaml").write_text(
        yaml.safe_dump(skills, sort_keys=False), encoding="utf-8"
    )

    tools_payload = [
        {
            "name": tool_name,
            "enabled": True,
            "mcp_server_url": None,
            "permissions": ["read", "write"],
        }
        for tool_name in tools
    ]
    (agent_dir / "tools.yaml").write_text(
        yaml.safe_dump(tools_payload, sort_keys=False), encoding="utf-8"
    )

    soul_template = (
        f"You are {name}. You are a helpful agent in the Hive team.\n"
        f"Your skills are: {', '.join(skills)}.\n"
        "You are collaborative and communicate clearly.\n"
    )
    (agent_dir / "soul.md").write_text(soul_template, encoding="utf-8")

    agent_config = {
        "name": name,
        "discord": {"token": discord_token},
    }
    if provider:
        if provider not in {"openai", "anthropic", "groq"}:
            raise click.UsageError("Provider must be one of: openai, anthropic, groq.")
        model = click.prompt("Model?", type=str)
        agent_config["llm"] = {
            "provider": provider,
            "model": model,
        }
    (agent_dir / "agent.yaml").write_text(
        yaml.safe_dump(agent_config, sort_keys=False), encoding="utf-8"
    )

    click.echo(
        f"Agent '{name}' created. Edit {agent_dir / 'soul.md'} to customize."
    )


@main.command("list")
def list_agents() -> None:
    """List configured agents."""
    agents = load_all_agents()
    if not agents:
        click.echo("No agents yet. Run 'hive add-agent' to create one.")
        return

    for agent in agents:
        tool_names = [tool.name for tool in agent.tools]
        click.echo(
            "Agent: "
            f"{agent.name} | "
            f"Skills: [{', '.join(agent.skills)}] | "
            f"Tools: [{', '.join(tool_names)}]"
        )


@main.command()
def config() -> None:
    """Open configuration."""
    config_dir = get_config_dir()
    settings_path = config_dir / "settings.yaml"
    if not settings_path.exists():
        provider = click.prompt(
            "Default LLM provider",
            type=click.Choice(["openai", "anthropic", "groq"], case_sensitive=False),
            default="openai",
            show_default=True,
        )
        model = click.prompt("Default LLM model", type=str, default="gpt-4o")
        guild_id = click.prompt("Discord guild ID", type=int)
        settings = {
            "default_llm": {"provider": provider, "model": model},
            "guild_id": guild_id,
        }
        settings_path.write_text(
            "# Hive Settings\n" + yaml.safe_dump(settings, sort_keys=False),
            encoding="utf-8",
        )
        env_path = Path(".env")
        if not env_path.exists():
            env_path.write_text("HIVE_LLM_API_KEY=\n", encoding="utf-8")
        click.echo("Config created at ~/.config/hive/settings.yaml")
        click.echo("Edit this file and fill in your values.")
        click.echo("Set HIVE_LLM_API_KEY in .env")
        return

    env_path = Path(".env")
    if not env_path.exists():
        env_path.write_text("HIVE_LLM_API_KEY=\n", encoding="utf-8")
    click.echo("Config already exists at ~/.config/hive/settings.yaml")
    click.echo("Set HIVE_LLM_API_KEY in .env")


@main.command()
def test() -> None:
    """Test LLM connectivity for all agents."""
    settings = load_settings()
    agents = load_all_agents()
    if not agents:
        click.echo("No agents yet. Run 'hive add-agent' to create one.")
        return

    async def run_tests() -> None:
        for agent in agents:
            llm_config = agent.llm or settings.default_llm
            client = HiveLLMClient(llm_config)
            click.echo(f"Testing {agent.name}...")
            await client.test_connection()

    asyncio.run(run_tests())


@main.command("tools")
def list_tools() -> None:
    """List registered tools and status."""
    agents = load_all_agents()
    if not agents:
        click.echo("No agents yet. Run 'hive add-agent' to create one.")
        return

    registry = ToolRegistry()
    for agent in agents:
        for tool in agent.tools:
            if registry.get_tool(tool.name) is None:
                registry.register(tool)

    mcp_bridge = MCPBridge(registry)
    tool_names = registry.list_tools()
    if not tool_names:
        click.echo("No tools registered.")
        return

    for name in tool_names:
        tool = registry.get_tool(name)
        if tool is None:
            continue
        enabled = "enabled" if tool.enabled else "disabled"
        permissions = ", ".join(tool.permissions)
        connected = "connected" if mcp_bridge.is_connected(name) else "not connected"
        click.echo(
            f"{tool.name} | {enabled} | permissions: [{permissions}] | {connected}"
        )


if __name__ == "__main__":
    main()
