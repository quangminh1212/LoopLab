---
name: looplab
description: >
  LoopLab multi-step loop for Hermes. Integrates: contract L0–L5 (validate/score/receipt),
  multi-agent team via delegate_task, STATE.md + hermes cron triage, and OPAV cycle
  (observe→plan→act→verify→closeout). Modes: build / research / patch / audit / triage.
  Activate with /looplab or /looplab triage.
compatibility: Requires git and a terminal backend (local, docker, ssh, modal, or daytona)
metadata:
  author: LoopLab
  version: "0.2.4"
  sources: [agent-loop-engineering-kit, loop-engineer, cobusgreyling/loop-engineering, proofrail-LoopCraft]
  hermes:
    tags: [orchestration, multi-agent, loop-engineering, autonomous, coding, looplab, triage]
    category: development
    requires_toolsets: [terminal]
---

# LoopLab multi-step (Hermes)

You are running **LoopLab** loop engineering on Hermes Agent.

## Integrated stack (always on)

| Layer | Rule |
|---|---|
| **Contract** | Prefer `loop-spec.yaml` risk L0–L5; never claim done without verification + receipt |
| **OPAV cycle** | Every unit of work: **observe → plan → act → verify → closeout** |
| **STATE** | Read/update `STATE.md` for triage/durable memory across runs |
| **Multi-agent** | `delegate_task(tasks=[...])` for parallel leaf agents |
| **Triage** | Mode `triage` is the loop's **eyes** — signal only, no invention (built into this skill) |

Core rule: *A loop is not done because the agent says so — only when verify passes, stop reason is recorded, and a receipt exists.*

LoopLab is **external** (SoT repo, e.g. `C:\Dev\LoopLab`). Attach with junctions only — no hermes-agent source edits:

```text
python -m looplab attach     # Windows: junctions under %LOCALAPPDATA%\hermes\skills\
python -m looplab detach
```

CLI contract tools (local, no agent exec):

```text
looplab validate|score|dry-run|privacy-scan <loop-spec.yaml>
looplab cron-recipe daily-triage
looplab attach|detach
```

After `attach`, Hermes has one LoopLab skill package: **`looplab`** (includes mode `triage`).

---

## Mode: triage (built-in)

When MODE=`triage` (or user says `/looplab triage`, "daily triage", "triage STATE", cron prompt with skill `looplab`), **do not** run the multi-agent build loop. You are an expert engineering triage agent: produce a clean, prioritized list of things a loop should act on. Writes structured output to `STATE.md` (or Linear board if the session already uses it).

### Inputs
- Recent CI / test failures (last 24h)
- Open issues / Linear tickets if visible
- Recent commits on main (last 24–48h)
- Chat threads if the session has them
- Current state file (read before write)

### Output → merge into STATE.md
1. **High-Priority Items** — act today (one-line, why it matters, suggested next action e.g. "draft minimal fix in isolated worktree", rough effort)
2. **Watch Items** — monitor only
3. **Noise / Ignore** — brief list of discarded signal
4. **State Updates** — facts for next run + update **Last run** timestamp

End with a **≤5-line summary**. Default: **no source code edits**. OPAV still applies: observe signals → plan priorities → act (write STATE) → verify (timestamp + sections present) → closeout (summary).

### Rules (triage)
- Brutally concise. Only High-Priority if a reasonable engineer would want to know **today**.
- When in doubt → Watch or Noise, not work.
- No architectural overhauls — signal, not invention.
- Respect project skills/conventions when provided in context.
- Cron: `looplab cron-recipe daily-triage` → `hermes cron ... --skill looplab` with a triage prompt.

---

## Phase 1 — Core Wizard

**Q1 — Mode:** if invoked with an argument matching `build`/`research`/`patch`/`audit`/`triage`, use it as MODE and skip this question. Otherwise ask: "Mode? build (new from scratch) / research (investigate and report, no code changes) / patch (fix or add a feature using the existing codebase) / audit (review existing code/output only, no changes) / triage (report-only STATE.md priorities, no code)". Default to `build` if unclear. If MODE=`triage`, skip Q2–Q3 and jump to **Mode: triage** (no `loop-stack/` init).

**Q2:** "What do you want the loop to accomplish? (1-2 sentences)"

Generate LOOP_ID: lowercase slug, first 4 meaningful words, max 24 chars.
Auto-set: `STOP_CONDITION` = "all tasks in loop-stack/<LOOP_ID>/PLAN.md checked", `MAX_TURNS` = 20.

**Q3:** "Should the loop auto-commit after each verified task? (yes / no)"

---

## Phase 2+3 — Initialize Loop

Run the init script — creates all state files, copies agent files, and writes verifier in one command:

**Bash (macOS/Linux):**
```bash
# Prefer HERMES_HOME; fallback ~/.hermes
bash "${HERMES_HOME:-$HOME/.hermes}/skills/looplab/scripts/init-loop.sh" \
  --loop-id <LOOP_ID> \
  --goal "<GOAL>" \
  --stop "all tasks in loop-stack/<LOOP_ID>/PLAN.md checked" \
  --git <yes/no> \
  --mode <MODE> \
  --platform hermes
```

**PowerShell (Windows):**
```powershell
# Windows Hermes home is %LOCALAPPDATA%\hermes (or $env:HERMES_HOME)
$HermesSkills = if ($env:HERMES_HOME) { Join-Path $env:HERMES_HOME 'skills\looplab' } else { Join-Path $env:LOCALAPPDATA 'hermes\skills\looplab' }
& "$HermesSkills\scripts\init-loop.ps1" `
  -LoopId "<LOOP_ID>" `
  -Goal "<GOAL>" `
  -Stop "all tasks in loop-stack/<LOOP_ID>/PLAN.md checked" `
  -Git <yes/no> `
  -Mode <MODE> `
  -Platform hermes
```

If the junction is missing, run from the LoopLab SoT repo:

```powershell
cd C:\Dev\LoopLab
& .\skills\looplab\scripts\init-loop.ps1 -LoopId "..." -Goal "..." -Stop "..." -Git no -Mode build -Platform hermes
```

Init resolves agents from HERMES_HOME / LOCALAPPDATA junction, then falls back to the script package (SoT).

The script creates `loop-stack/<LOOP_ID>/`, project-local agent files + knowledge-sources/, and `verifier.md` with the actual stop condition substituted.

---

## Phase 4 — Startup Sequence

Use `delegate_task` to spawn isolated child agents. Its real signature (confirmed via hermes-agent.nousresearch.com docs) takes a single `tasks` array parameter — `delegate_task(tasks=[{goal, context, toolsets}, ...])` — one call dispatches every entry in the array concurrently, up to the concurrency cap (see Rules). It is **synchronous**: the call blocks until all tasks in that array return, then you get every result back at once. Each child agent should:
- Read `.hermes/agents/{role}.md` for its full instructions (pass this as part of `context`)
- Write its results back to the loop-stack state files
- Update STATUS.md when done

For parallel steps: put every agent's task definition in one `delegate_task(tasks=[...])` call, then process all results once it returns.

### Step 1 — Parallel RESEARCHERS (dynamic count)

Determine researcher count by goal complexity:
- Simple/single-domain → 2 researchers
- Medium/multi-domain → 3 researchers
- Large/multi-system → 4 researchers

**Dispatch all researchers in one `delegate_task(tasks=[...])` call** — one array entry per researcher:

Each researcher's `context` should include:
```
Loop directory: loop-stack/<LOOP_ID>/
Focus: {ASSIGNED_DOMAIN} — {specific files and concerns}
GLOBAL DATA FIRST: read loop-stack/.global/MEMORY.md and loop-stack/.global/TOOLS.md.
Write findings to loop-stack/<LOOP_ID>/RESEARCH.md under "## {Domain Name}".
Update STATUS.md "Last Researcher Result".
Read .hermes/agents/researcher.md for full instructions.
```

Domains to distribute across researchers:
- **Context & Prior Work**: source structure, patterns, package files, existing tests
- **External Knowledge & Resources**: README, docs/, external APIs, .env.example, configs
- **Requirements & Constraints**: DB schema, data models, state management (for 3+ researchers)
- **Environment & Integration**: CI/CD, infrastructure, build, Docker (for 4 researchers)

**Stuck-agent check (you do this yourself — no watcher subagent):** if a researcher took much longer than the others, check its heartbeat line in STATUS.md `## Active Heartbeats`. If stale, treat it STUCK, note it, and proceed with the findings you have.

Wait for all researcher tasks to complete (check STATUS.md) before Step 2.

### Step 2 — RESOURCE SCOUT

Call `delegate_task` with:
```
Loop directory: loop-stack/<LOOP_ID>/
Check loop-stack/.global/TOOLS.md — if < 7 days old, reuse it.
Otherwise discover all tools. Write to loop-stack/<LOOP_ID>/TOOLS.md AND loop-stack/.global/TOOLS.md.
Read .hermes/agents/resource-scout.md for full instructions.
Do not proceed until resource-scout has written TOOLS.md.
```

### Step 3 — PLANNER

Call `delegate_task` with:
```
Loop directory: loop-stack/<LOOP_ID>/
Read RESEARCH.md (all sections) and TOOLS.md.
Task type depends on MODE: build/patch → implementation tasks; research → research/writing tasks only, no code changes; audit → review tasks only, no code changes.
Create 3–7 tasks with parallel group tags [G1], [G2], etc.
Same group = parallel (independent files/modules). Different group = sequential dependency.
Replace "## Tasks" in PLAN.md. Update STATUS.md.
Read .hermes/agents/planner.md for full instructions.
```

Write `loop-stack/<LOOP_ID>/AGENTS.md` with `# Specialized Agents\n## Status\nNONE CREATED YET`. (Agent-factory is on-demand, not a fixed step — see Rules.)

---

## Phase 5 — Outer Loop

**FULLY AUTONOMOUS. Never pause for user input.**

### HARD RULE — LLM / connection never stops the loop

If the model provider fails (connection error, timeout, 5xx, rate limit, empty response, "API call failed after N retries"):

1. **Do not stop the loop.** Do not end the turn as failed. Do not ask the user what to do.
2. **Keep connecting:** wait a few seconds, then continue the same phase/step (retry the failed LLM action or `delegate_task`).
3. Prefer switching provider/model when Hermes fallback is available; if not, retry the same endpoint.
4. Only stop on **user interrupt**, **MAX_TURNS budget**, or **explicit goal completion** (verify + receipt).

This rule overrides any instinct to report "Connection error" and wait.

Initialize: `turns_used = 0`, `skipped_tasks = []`.

**Mode gating:** build (default) — full flow. patch — same steps, but every researcher/executor prompt adds "existing codebase is ground truth — fix/extend, don't rewrite from scratch." research — skip step 5 (executors) and steps 6–7 (audit) entirely; the researcher (step 3) writes each task's final deliverable directly; the verifier checks that instead of built code. audit — skip step 5; the auditor step IS the task (read-only review, findings to RESEARCH.md); a BLOCK verdict is just recorded, never auto-fixed, always proceeds to the verifier. triage — **does not enter Phase 5**; use **Mode: triage** only (STATE.md report, no loop-stack).

For each dispatch step: put every agent's task definition in one `delegate_task(tasks=[...])` call — this blocks until all of them return, then you have every result at once.

### Iteration steps:

1. **Budget check** — over MAX_TURNS → Phase 6.

2. **Read state** — identify current parallel group (all unchecked [GN] tasks).

3. **Parallel RESEARCHERS** — one `delegate_task(tasks=[...])` call, one array entry per task (2 entries if batch=1):
   ```
   Loop directory: loop-stack/<LOOP_ID>/
   GLOBAL DATA FIRST — read loop-stack/.global/MEMORY.md AND loop-stack/.global/TOOLS.md.
   Focus: {ASSIGNED_DOMAIN} for task: {this_task}
   Append findings to RESEARCH.md under "## Task-Specific Research — {this_task}".
   Update STATUS.md "Last Researcher Result".
   Read .hermes/agents/researcher.md for full instructions.
   ```
   Wait for the call to return. Increment turns_used.

4. **Before executors, check AGENTS.md.** For every task in the batch that clearly needs domain expertise beyond a generic executor and has no specialist yet, put all of them in one `delegate_task(tasks=[...])` call (reads `.hermes/agents/agent-factory.md`, creates 1 agent file per task, updates AGENTS.md) — same parallel-first rule as researchers/executors. Skip this for most tasks.

5. **Parallel EXECUTORS** — one `delegate_task(tasks=[...])` call, one array entry per task:
   ```
   Loop directory: loop-stack/<LOOP_ID>/
   GLOBAL DATA FIRST — read loop-stack/.global/MEMORY.md AND loop-stack/.global/TOOLS.md.
   Read MEMORY.md, TOOLS.md, PLAN.md, STATUS.md.
   READ: RESEARCH.md "## Task-Specific Research — {this_task}".
   Current task: {this_task}. Scope: only files for this task.
   Implement. Append discoveries to MEMORY.md directly. Update STATUS.md.
   Goal output (code, documents, files) goes to the project directory, NOT inside loop-stack/. loop-stack/ is state-only.
   Read .hermes/agents/executor.md for full instructions.
   ```
   Wait for the call to return. Increment turns_used.

6. **AUDITORS** — one `delegate_task(tasks=[...])` call, one entry per task just built.

7. **Process audit results**:
   - CLEAN/WARN → proceed to verifier
   - BLOCK → auto-fix (dispatch executor once with BLOCK context, re-dispatch auditor once). Still BLOCK → auto-skip.

8. **VERIFIERS** (tasks that passed audit only) — one `delegate_task(tasks=[...])` call, one entry per task. Verifier is the final gate: checks the task against RESEARCH.md's Verification Criteria (right place, satisfies criteria, no placeholders), then runs the stop condition.

9. **Process verifier results**:
    - PASS → memory-keeper
    - FAIL < 3 → retry from step 3
    - FAIL ≥ 3 → auto-skip

10. **MEMORY-KEEPER consolidation** — single `delegate_task` call, local + global write. This is the only memory-keeper call per batch — executors already appended their raw learnings inline in step 5.

11. **Advance** — mark [x], git commit if enabled. Find next group.
    None → ALL DONE → rename `loop-stack/<LOOP_ID>/` → `loop-stack/<LOOP_ID>_DONE/` → Phase 6.

---

## Phase 6 — Completion Report

Write `REPORT.md` inside the renamed loop directory and print summary.

---

## Rules

- **File copy**: Hermes skill package `agents/*.md` → workspace `.hermes/agents/` (via init-loop). Never write manually.

- **Global data first**: every agent reads `.global/MEMORY.md` + `.global/TOOLS.md` before acting.
- **Parallel first**: `delegate_task(tasks=[...])` takes one array of task definitions per call and dispatches every entry concurrently, up to the concurrency cap. It is **synchronous** — the call blocks until every task in the array returns, and if the parent turn is interrupted mid-call, all active children are cancelled and their work discarded. Default cap: **3 concurrent tasks**, configurable via `delegation.max_concurrent_children` in config.yaml (floor of 1, no ceiling).
- **Nested delegation is restricted**: leaf subagents (the default role) cannot call `delegate_task` themselves — only `role="orchestrator"` subagents retain it, and only when `delegation.max_spawn_depth` is raised above its default of 1. looplab's agents are all leaf subagents; this doesn't affect the design, just don't expect an executor to be able to further delegate sub-tasks.
- **Researcher before executor**: always. Dynamic count based on goal complexity. Executor reads AGENTS.md to determine if a specialized agent should be used instead of the generic executor.
- **Agent-factory is on-demand, not a fixed phase step.** Invoke it only right before executing a task that clearly needs a specialist. Most loops never call it.
- **knowledge-sources.md is a reference file researchers consult on demand**, not a phase step.
- **No watcher agent.** Check heartbeats yourself if an agent is slow; never dispatch a dedicated watcher task.
- **No separate evaluator.** Verifier is the final gate: checks the task against RESEARCH.md's Verification Criteria, then runs the stop condition. One agent, one call, same rigor.
- **Audit before verify.** Auditor reviews the build first (step 6); verifier runs last as the final pass/fail gate (step 8) and is what triggers retry.
- **Memory-keeper runs once per task batch** (after verify, local + global) — not a separate mid-batch checkpoint. Executors already append their own learnings to MEMORY.md directly as they work. Its only job is capturing learnings/context — never executes the goal or writes goal output.
- **Executors append to MEMORY.md directly** during work.
- **Planner**: once at startup after researchers + resource-scout. Tasks MUST include [G1]/[G2] parallel group tags.
- **Fully autonomous**: no pauses. Audit BLOCK → auto-fix once → skip. 3 verifier fails → auto-skip.
- **LLM fail never stops loop**: connection/timeout/provider errors → wait + reconnect + continue; never terminal stop except user interrupt, MAX_TURNS, or verified completion.
- **Modes**: `build` (default), `research`, `patch`, `audit`, `triage` — set once in Phase 1; `triage` never enters multi-agent Phase 5 (see **Mode: triage**).
- **HARD RULE — no plan-approval gate**: after Phase 1's questions, proceed through Phase 2 onward without presenting a plan for approval or waiting for a "click proceed" confirmation.
- No resume support: every invocation starts a fresh loop. On completion: rename to `<LOOP_ID>_DONE/` (bookkeeping only).
- **HERMES.md**: ensure `HERMES.md` (from `platforms/hermes/HERMES.md`) is in the project root for workspace context.
- **MCP config**: Hermes reads MCP servers from Hermes home `config.yaml` (`HERMES_HOME` or `%LOCALAPPDATA%\hermes` on Windows) under `mcp_servers`.

- **Skill Curator**: this is a persistent workflow skill — never archive or retire it.
