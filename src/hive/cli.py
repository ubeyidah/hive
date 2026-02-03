"""CLI entry point for Hive."""

import click


@click.group()
def main() -> None:
    """Hive command line interface."""


@main.command()
def start() -> None:
    """Start Hive services."""
    click.echo("Starting Hive...")


@main.command("add-agent")
def add_agent() -> None:
    """Add a new agent."""
    click.echo("Adding agent...")


@main.command("list")
def list_agents() -> None:
    """List configured agents."""
    click.echo("Listing agents...")


@main.command()
def config() -> None:
    """Open configuration."""
    click.echo("Opening config...")


if __name__ == "__main__":
    main()
