# Hive Guide

## What is Hive
Hive is a multi-agent Discord system where each agent runs as its own bot. Agents share a common context, use an LLM through LiteLLM, and can call external tools via MCP when permitted.

## Requirements
- Python 3.14+
- A Discord account
- Discord bot tokens
- An LLM API key (e.g., OpenAI, Anthropic, Groq)

Discord bot token steps:
1. Go to the Discord Developer Portal.
2. Click "New Application" and create an app.
3. Open the "Bot" tab and click "Add Bot".
4. Under "Privileged Gateway Intents", enable "Message Content".
5. Click "Reset Token" and copy the bot token.
6. Invite the bot to your server using the OAuth2 URL Generator with "bot" scope and appropriate permissions.

LLM API key:
1. OpenAI: create an API key in your OpenAI account.
2. Anthropic: create an API key in the Anthropic console.
3. Groq: create an API key in the Groq console.

## Installation
1. Clone or download the repository.
2. Create and activate a virtual environment: `uv venv .venv && source .venv/bin/activate`
3. Install in editable mode: `uv pip install -e .`

## First Setup
1. Run `hive config`.
2. It creates `~/.config/hive/settings.yaml` and a local `.env`.
3. Edit `settings.yaml` and `.env`.
4. Create your first agent with `hive add-agent`.

`settings.yaml` structure:
```yaml
# Hive Settings
# default_llm defines the shared default model
# guild_id is the Discord server ID for your bots

default_llm:
  provider: openai
  model: gpt-4o

guild_id: 123456789012345678
```

`.env` for API key:
```bash
HIVE_LLM_API_KEY=your_api_key_here
```

`hive add-agent` prompts:
- Agent name
- Discord bot token
- Skills list
- Tools list
- Optional LLM provider/model override

Files created for each agent in `~/.config/hive/agents/{name}/`:
- `agent.yaml`
- `skills.yaml`
- `tools.yaml`
- `soul.md`

## Agent Configuration
Each agent lives at `~/.config/hive/agents/{name}/`.

`agent.yaml` example:
```yaml
name: writer
discord:
  token: your_discord_bot_token
llm:
  provider: openai
  model: gpt-4o
```

`skills.yaml` example:
```yaml
- post writing
- research
```

`tools.yaml` example:
```yaml
- name: gmail
  enabled: true
  mcp_server_url: http://localhost:3001
  permissions:
  - read
  - send
```

`soul.md` example:
```
You are writer. You are a helpful agent in the Hive team.
Your skills are: post writing, research.
You are collaborative and communicate clearly.
```

Tips for a good soul:
- Describe the agent’s mission clearly.
- Mention the type of tasks it excels at.
- Keep it short and actionable.

## Settings Configuration
`~/.config/hive/settings.yaml` contains shared defaults.

Fields:
- `default_llm`: the fallback LLM for agents without their own `llm` block
- `guild_id`: the Discord server ID where bots should run

Supported providers:
- `openai`
- `anthropic`
- `groq`

## Tools
Hive tools are configured per agent and enforced by permissions.

Permissions:
- `read`
- `write`
- `send`
- `delete`

Enable/disable tools:
- Set `enabled: true` or `enabled: false` per tool in `tools.yaml`.

Tool calls format:
```
[TOOL: tool_name | action: read/write/send | params: key=value, key=value]
```

Example tool call:
```
[TOOL: gmail | action: send | params: to=user@email.com, subject=Hello, body=Hi there]
```

## Running Hive
- Start bots: `hive start`
- Test LLM connectivity: `hive test`
- List agents: `hive list`
- List tools: `hive tools`
- Stop: Ctrl+C

## Using Hive in Discord
- Mention an agent with `@agent_name` to force a reply.
- Agents decide to respond if not mentioned based on their soul and the message.
- Agents share context, so they can collaborate across tasks.

Example:
```text
User: @writer draft a post about our new launch
Writer: Drafting now…
Writer: [TOOL: gmail | action: send | params: to=team@email.com, subject=Draft, body=...]
```

## Adding More Agents
- Run `hive add-agent` again for each new agent.
- Agents see all teammates in their system prompt.
- Use clear skills and tools to help routing.

## Troubleshooting
Bot not responding: Ensure the bot is invited to the server, has permissions, and the Message Content intent is enabled. Verify the bot token in `agent.yaml`.

LLM connection failing: Ensure `HIVE_LLM_API_KEY` is set in `.env` and verify provider/model names.

Tool permission errors: Check `tools.yaml` for `enabled` and correct permissions.

Config file not found: Run `hive config` to create settings.

Discord token errors: Regenerate the token and update `agent.yaml`.

## Project Structure
```
.
├── AGENTS.md
├── ARCHITECTURE.md
├── GUIDE.md
├── README.md
├── main.py
├── pyproject.toml
├── src
│   └── hive
│       ├── __init__.py
│       ├── cli.py
│       ├── agent
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── context.py
│       │   └── manager.py
│       ├── config
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   └── schema.py
│       ├── discord
│       │   ├── __init__.py
│       │   ├── bot.py
│       │   └── bot_manager.py
│       ├── llm
│       │   ├── __init__.py
│       │   ├── client.py
│       │   └── prompt_builder.py
│       └── tools
│           ├── __init__.py
│           ├── executor.py
│           ├── mcp_bridge.py
│           └── registry.py
└── uv.lock
```
