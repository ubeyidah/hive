# Architecture

## Overview
This project is a multi-agent Discord system where each agent is its own bot. Agents share context, call LLMs via LiteLLM, and optionally invoke MCP tools. Results are posted back to Discord, where other agents can react and continue the task loop.

## System Flow (YAML)
```yaml
developer:
  writes_in: discord_channel
discord_channel:
  visible_to: [all_agents]
agents:
  - bot: each_agent
    brain:
      llm: litellm
      tools: mcp_tools
    outputs_to: discord_channel
loop:
  continues_until: task_done
```

## Planned Project Layout
```
project-root/
├── config/
│   ├── agents.yaml
│   ├── tools.yaml
│   └── settings.yaml
├── core/
│   ├── agent.py
│   ├── llm_client.py
│   ├── context_manager.py
│   ├── tool_registry.py
│   └── permission.py
├── discord/
│   ├── bot_manager.py
│   ├── event_handler.py
│   └── message_formatter.py
├── tools/
│   ├── mcp_bridge.py
│   ├── email.py
│   ├── calendar.py
│   └── ...
├── agents/
├── main.py
└── cli.py
```

## Key Components
- **Agent class**: Holds name, personality, skills, memory, and tool access. Decides when to act or delegate.
- **Context Manager**: Shared conversation history so all agents stay in sync.
- **Bot Manager**: Runs one Discord bot per agent, concurrently via async Python.
- **Tool Registry + MCP Bridge**: Enforces per-agent permissions and routes tool calls to MCP servers.
- **CLI**: Manages lifecycle and agent config (e.g., `myteam start`, `myteam add-agent`, `myteam list`).

## Mention-Triggered Flow
1. A user mentions an agent in Discord.
2. The event handler records it in the context manager.
3. The target agent runs with full context and available tools.
4. The agent may call MCP tools, then posts results.
5. Other agents can react, review, or publish.
