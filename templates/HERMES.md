# HERMES.md — LoopLab project context for Hermes Agent

This project uses **LoopLab** loop engineering.

## Defaults
- Risk ladder: L0 advisory → L5 money/secrets/prod (block without approval)
- Cycle: observe → plan → act → verify → closeout
- Durable state: `STATE.md`
- Contract: `loop-spec.yaml` (validate with `looplab validate`)
- Skill: `looplab` (modes: build|research|patch|audit|triage; install via `looplab attach`)

## Hard rules
1. Do not mark a loop done without verification + receipt.
2. Cron jobs start with `--deliver local` until trusted.
3. L3+ file edits use git worktree + tests + verifier subagent.
4. Never write secrets into STATE.md or receipts.
5. Prefer `delegate_task` for implementer vs verifier split.

## Commands
```text
/looplab
/goal <bounded goal with stop condition>
```
