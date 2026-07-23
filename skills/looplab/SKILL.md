---
name: looplab
description: >
  LoopLab loop engineering for Hermes. Design or run a bounded loop:
  observe → plan → act → verify → closeout. Uses loop-spec.yaml, STATE.md,
  receipts, risk classes L0–L5, and optional delegate_task split
  (implementer vs verifier). Modes: design, run, triage, goal.
---

# LoopLab (Hermes)

You are operating inside **LoopLab** loop engineering for Hermes Agent.

## Invocation

User may say `/looplab`, `/looplab design`, `/looplab run`, `/looplab triage`, or `/looplab goal <text>`.

## Core rule

> A loop is not done because you say it is done. It is done when verification passes, stop reason is recorded, and a receipt exists.

## Cycle (every run)

1. **Observe** — read `loop-spec.yaml` (if present), `STATE.md`, goal, repo constraints (`HERMES.md` / `AGENTS.md`).
2. **Plan** — list atomic steps, risk class, isolation, verification checks, stop conditions.
3. **Act** — smallest safe action only; respect `tools.forbidden_actions`.
4. **Verify** — run deterministic checks (tests, file exists, lint) before claiming success.
5. **Closeout** — update `STATE.md`, write receipt under `receipts/`, report stop reason.

## Modes

### design
- If no `loop-spec.yaml`, create one from the user goal (risk L0–L2 default).
- Prefer structure compatible with LoopLab CLI (`looplab validate` / `score` / `dry-run`).
- Do **not** enable cron/webhook until dry-run + manual run succeed.

### run
- Load contract; refuse to exceed risk_class without human gate text.
- For L3+ edits: use git worktree if available; never force-push.
- Split work with `delegate_task` when possible:
  - implementer: terminal + file tools
  - verifier: review-only, no edits
- Stop on max_iterations / repeated error / verification fail.

### triage
- Report-only unless user explicitly allows fixes.
- Merge findings into `STATE.md` High Priority / Watch List.
- End with a 5-line summary. No source edits by default.

### goal
- Keep the goal alive across turns until verification passes (Hermes `/goal` style).
- Re-read STATE each turn; do not reset progress.

## Risk classes

| Class | Meaning | Default |
|---|---|---|
| L0 | Advisory one-off | direct |
| L1 | Repeated read-only report | dry-run → manual |
| L2 | Write local reports/state | active + receipt |
| L3 | Edit repo | worktree + tests + verifier |
| L4 | External side effects | approval every run |
| L5 | Money/secrets/delete/prod | block unless explicit approval + rollback |

## Receipt template

Write `receipts/<loop-name>.latest.md`:

```markdown
# Loop Run Receipt — <name>
- Status: PASS|FAIL
- Mode: RUN|DRY_RUN|TRIAGE
- Risk: Lx
- Verification: PASS|FAIL
- Stop reason: ...
- External side effects: none|...
```

## Forbidden unless approved

- delete production data
- expose secrets into chat/STATE/receipt
- public posting / payments / production deploy
- unattended cron with L4/L5 risk

## Hermes mapping

| Loop piece | Hermes shape |
|---|---|
| Trigger | chat, `hermes cron`, webhook, kanban |
| State | STATE.md, memory, session search |
| Act | tools + optional `delegate_task` |
| Verify | tests / smoke / verifier subagent |
| Schedule | `hermes cron create ... --deliver local` first |
