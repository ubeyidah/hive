# Openbuden

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.14%2B-blue.svg)

Openbuden is a multi-agent Discord system where each agent runs as its own bot, shares a common context, and can call tools through MCP. It is designed for teams that want collaborative agents that can reason together while staying specialized.

## Highlights
- One Discord bot per agent
- Shared conversation context across all agents
- LLM-backed decision making via LiteLLM
- Tool system with permissions and MCP bridge
- Simple CLI to configure, test, and run

## Requirements
- Python 3.14+
- A Discord account and server
- Discord bot tokens for each agent
- An LLM API key (OpenAI, Anthropic, or Groq)

## Quickstart
1. Create and activate a virtual environment:
   ```bash
   uv venv .venv && source .venv/bin/activate
   ```
2. Install in editable mode:
   ```bash
   uv pip install -e .
   ```
3. Create base configuration:
   ```bash
   openbuden config
   ```
4. Add your first agent:
   ```bash
   openbuden add-agent
   ```
5. Start Openbuden:
   ```bash
   openbuden start
   ```

## Configuration
Openbuden uses two config locations:
- `~/.config/openbuden/settings.yaml` for shared defaults
- `.env` in the project root for `OPENBUDEN_LLM_API_KEY`

To create them, run:
```bash
openbuden config
```

## Common Commands
- `openbuden config` — create or update the base settings
- `openbuden add-agent` — create a new agent
- `openbuden list` — list agents and their tools
- `openbuden tools` — show registered tools and permissions
- `openbuden test` — verify LLM connectivity
- `openbuden start` — start all Discord bots

## Documentation
See `GUIDE.md` for full documentation, examples, and troubleshooting.

## Project Structure
```
src/openbuden/
  agent/      # Agent logic and shared context
  config/     # YAML config loading and schemas
  discord/    # Discord bot runtime
  llm/        # LiteLLM client and prompt builder
  tools/      # Tool registry, MCP bridge, executor
```

## License
TBD
