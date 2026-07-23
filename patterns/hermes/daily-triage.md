# Daily Triage — Hermes Agent

Scheduling runs on the Hermes **gateway** (`hermes cron`). LoopLab ships triage as **mode `triage` inside skill `looplab`** (no separate `loop-triage` package). A full L1 daily-triage loop needs a scheduled job + `looplab` + a `STATE.md` file.

Optional **channel delivery** (Feishu, Slack, Telegram, Discord, WhatsApp, SMS) is the main reason to run triage here — the same cron job can post its summary into any connected home channel.

## Prerequisites

1. [Hermes Agent](https://hermes-agent.nousresearch.com/docs) installed and configured (`hermes setup`).
2. `STATE.md` at the repo root — copy from LoopLab `templates/STATE.md` / `templates/STATE.md.template`.
3. Attach LoopLab skill (junction only):

```powershell
cd C:\Dev\LoopLab
python -m looplab attach
# or: powershell -File .\scripts\install.ps1
```

Verify:

```bash
hermes skills list | grep looplab
# Windows Hermes home skills: %LOCALAPPDATA%\hermes\skills\looplab
```

## Report-Only (Week 1)

Isolated cron job: fresh session each run, writes to `STATE.md`, no code edits. Delivery pinned to `local` so nothing leaks into the human's DM history until you trust the output.

```bash
hermes cron create "0 7 * * 1-5" \
  --name "Daily triage" \
  --deliver local \
  --skill looplab \
  --workdir "$PWD" \
  "Run /looplab triage. Read STATE.md. Merge findings into High Priority and Watch List. Update Last run timestamp. Do not edit source code. End with a 5-line summary."
```

Or print the recipe:

```powershell
python -m looplab cron-recipe daily-triage
```

- `--workdir "$PWD"` injects project context and pins terminal cwd.
- `--deliver local` writes output to Hermes cron output only. Swap for a home channel when trusted.
- Repeat `--skill` to attach extra skills if needed (e.g. github).

Faster cadence during active periods:

```bash
hermes cron create "0 */2 * * *" \
  --name "Triage pulse" \
  --deliver local \
  --skill looplab \
  --workdir "$PWD" \
  "Run /looplab triage. Report obvious small wins only. Update STATE.md. No code changes."
```

## With Small Auto-Fixes (Week 3+)

Use `delegate_task` after triage, or chain two cron jobs with `--context-from`.

```bash
TRIAGE_ID=$(hermes cron create "0 7 * * 1-5" \
  --name "Triage + propose" \
  --deliver local \
  --skill looplab \
  --workdir "$PWD" \
  "Run /looplab triage. For high-priority single-file bugfixes, propose a minimal diff in a fenced patch block. Update STATE.md. Do not apply the patch." \
  | tail -1)

hermes cron create "5 7 * * 1-5" \
  --name "Triage → apply + verify" \
  --deliver local \
  --skill looplab \
  --workdir "$PWD" \
  "Read the injected triage output. If it contains a fenced patch: create an isolated git worktree, apply the patch, run tests, then delegate a verifier subagent. Update STATE.md."
```

```bash
hermes cron edit <fixer-job-id> --context-from "$TRIAGE_ID"
```

## Event-Triggered Triage

```bash
curl -X POST http://127.0.0.1:8765/hooks/agent \
  -H "Authorization: Bearer $HERMES_WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Run /looplab triage on recent CI failures. Update STATE.md. Report only.",
    "name": "CI triage",
    "deliver": "local"
  }'
```

## Verification Split

| Role | Hermes shape |
|------|--------------|
| Triage | skill `looplab` mode triage + `hermes cron` `--deliver local` |
| Implementer | Main agent or `delegate_task` in a `git worktree` |
| Verifier | Second `delegate_task` or chained cron job |

## Safety (L1 defaults)

- `--deliver local` until you trust output.
- Week one: **report-only**; human reads `STATE.md`.
- Approvals: `hermes config set approvals.mode smart` if needed.

## Operations

```bash
hermes cron list
hermes cron status
hermes cron run <job-id>
hermes cron pause <job-id>
hermes cron resume <job-id>
hermes cron remove <job-id>
```

## References

- LoopLab skill: `skills/looplab/SKILL.md` (section **Mode: triage**)
- [Hermes docs](https://hermes-agent.nousresearch.com/docs)
