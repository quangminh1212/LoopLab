# Loop Engineer

When the user asks to run an autonomous loop, orchestrate a multi-agent team,
or start a goal-driven task loop, activate the loop-engineer skill.

The skill is installed at `~/.hermes/skills/loop-engineer/SKILL.md`.

## Activation

Type `/loop-engineer` in any Hermes session, or simply describe a multi-step goal —
the agent will activate the skill automatically via progressive disclosure.

Examples:
- "I want to run an autonomous loop to add authentication to my API."
- "Help me orchestrate a multi-agent team to refactor this codebase."
- "Start a loop-engineer session and help me build X."

## How subagents work

Hermes uses `delegate_task` to spawn isolated child agents for parallel workstreams.
Multiple tasks in the same [GN] group are dispatched simultaneously.
The main agent waits for all children to write to STATUS.md before advancing.
Agent instruction files live in `.hermes/agents/` in the workspace (copied from the global skill).

## State files

All loop state lives in `loop-stack/<LOOP_ID>/`:
- `PLAN.md` — goal, tasks with [G1]/[G2] parallel group tags, stop condition
- `STATUS.md` — current state, attempts, last results from each agent
- `MEMORY.md` — accumulated learnings (grows smarter each iteration)
- `TOOLS.md` — discovered MCP servers, skills, plugins, project tooling
- `RESEARCH.md` — researcher findings per task
- `AGENTS.md` — specialized agents created by agent-factory after planning

`loop-stack/.global/` — shared across all loops in this project:
- `MEMORY.md` — cross-loop project learnings
- `TOOLS.md` — cached tool discovery (7-day TTL)

## Configuration paths

Skills (global):               ~/.hermes/skills/
Skills (workspace):            .agents/skills/          (agentskills.io standard)
MCP servers:                   ~/.hermes/config.yaml    (under `mcp_servers` key)
Config (all settings):         ~/.hermes/config.yaml
Secrets / API keys:            ~/.hermes/.env
Agent personality:             ~/.hermes/SOUL.md
Agent instruction files:       .hermes/agents/          (workspace, set up by the skill)

MCP config format:
```yaml
mcp_servers:
  my-server:
    command: npx
    args: ["-y", "@my/mcp-server"]
    env:
      MY_API_KEY: "${MY_API_KEY}"
  remote-server:
    url: https://mcp.example.com/sse
    headers:
      Authorization: "Bearer ${API_TOKEN}"
```

Reload MCP connections after editing: `/reload-mcp`

## Useful slash commands

- `/loop-engineer` — activate the skill
- `/reload-mcp`   — refresh MCP connections after config change
- `/skills`       — view and manage installed skills
- `/learn [src]`  — teach Hermes a new workflow from code, docs, or URLs
- `hermes config` — view or edit configuration from the terminal

## Hermes context file priority

Files auto-injected as project context (first match wins):
1. `.hermes.md` or `HERMES.md` (this file) — highest priority
2. `AGENTS.md`
3. `CLAUDE.md`
4. `.cursorrules`

`SOUL.md` in `~/.hermes/` sets global personality (independent of project context).
