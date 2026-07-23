"""Default templates for init / project scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from looplab.io_util import dump_yaml

DEFAULT_LOOP_SPEC: dict[str, Any] = {
    "schema_version": "1.0",
    "name": "example-loop",
    "goal": "Describe the bounded result this loop should produce.",
    "risk_class": "L1",
    "trigger": {
        "type": "manual",
        "schedule": None,
        "timezone": None,
    },
    "inputs": {
        "required": ["source to inspect"],
        "optional": [],
    },
    "state": {
        "backend": "file",
        "location": "STATE.md",
        "read_before_run": True,
        "update_after_run": True,
    },
    "tools": {
        "allowed": ["read_files", "search_files", "write_report", "terminal_readonly"],
        "forbidden_actions": [
            "delete_files",
            "access_secrets",
            "public_posting",
            "production_deploy",
            "payments",
        ],
    },
    "isolation": {
        "mode": "read_only",
        "notes": "Start read-only until receipt proves the loop is bounded.",
    },
    "verification": {
        "deterministic_checks": [
            {
                "name": "receipt_exists",
                "method": "check output receipt path exists",
                "pass_condition": "receipt includes stop_reason",
            }
        ],
        "review_checks": [
            {
                "name": "human_readability",
                "reviewer": "human",
                "rubric": "Can a human understand the receipt in two minutes?",
            }
        ],
        "definition_of_done": [
            "receipt written",
            "STATE.md updated",
            "no forbidden action attempted",
        ],
    },
    "stop_conditions": {
        "max_iterations": 3,
        "max_runtime_minutes": 30,
        "success_signal": "receipt_written",
        "failure_policy": "stop_and_report",
        "stop_on_repeated_error": True,
        "rationale": "Three iterations enough for L1 read-only loops before stop_and_report.",
    },
    "human_gate": {
        "required_for": [
            "deletion",
            "secrets",
            "public_posting",
            "production_deploy",
            "payments",
        ],
        "approval_format": "APPROVE LOOP ACTION: <action> / <scope> / <rollback>",
    },
    "outputs": {
        "artifacts": ["reports/example-loop.md"],
    },
    "receipt": {
        "required": True,
        "path": "receipts/example-loop.latest.md",
    },
    "cycle": [
        "observe",
        "plan",
        "act",
        "verify",
        "closeout",
    ],
    "hermes": {
        "skill": "looplab",
        "deliver": "local",
        "delegate": True,
    },
}

STATE_MD = """# STATE.md — LoopLab durable loop state

> Read before every run. Update after every run. Do not put secrets here.

## Loop
- Name:
- Last run:
- Last status: never

## High Priority
- (none)

## Watch List
- (none)

## Last findings
- (none)

## Flags
- loop-pause-all: false
"""

HERMES_MD = """# HERMES.md — LoopLab project context for Hermes Agent

This project uses **LoopLab** loop engineering.

## Defaults
- Risk ladder: L0 advisory → L5 money/secrets/prod (block without approval)
- Cycle: observe → plan → act → verify → closeout
- Durable state: `STATE.md`
- Contract: `loop-spec.yaml` (validate with `looplab validate`)
- Skill: `looplab` (modes build|research|patch|audit|triage; install via `looplab attach`)

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
"""

ACTIVATION_MD = """# Hermes activation plan

Fill only after dry-run + one clean manual read-only Hermes run.

## Loop
- Spec path:
- Risk class:
- Score:

## Manual run evidence
- Date:
- Receipt path:
- Verification result:
- Unexpected side effects:

## Proposed automation
- [ ] none (keep manual)
- [ ] hermes cron (schedule: )
- [ ] webhook
- [ ] kanban

## Deliver
- Week 1: `local` only
- Week 2+: channel name (optional):

## Rollback
- How to pause:
- How to remove job:
"""


def write_init_spec(path: str | Path, *, name: str | None = None) -> Path:
    p = Path(path)
    data = dict(DEFAULT_LOOP_SPEC)
    if name:
        data["name"] = name
        data["receipt"] = dict(data["receipt"])
        data["receipt"]["path"] = f"receipts/{name}.latest.md"
        data["outputs"] = dict(data["outputs"])
        data["outputs"]["artifacts"] = [f"reports/{name}.md"]
    dump_yaml(data, p)
    return p


def write_project_scaffold(root: str | Path) -> list[Path]:
    root = Path(root)
    written: list[Path] = []
    root.mkdir(parents=True, exist_ok=True)

    spec = write_init_spec(root / "loop-spec.yaml")
    written.append(spec)

    state = root / "STATE.md"
    if not state.exists():
        state.write_text(STATE_MD, encoding="utf-8")
        written.append(state)

    hermes = root / "HERMES.md"
    if not hermes.exists():
        hermes.write_text(HERMES_MD, encoding="utf-8")
        written.append(hermes)

    act = root / "activation-plan.md"
    if not act.exists():
        act.write_text(ACTIVATION_MD, encoding="utf-8")
        written.append(act)

    for d in ("receipts", "reports", "state"):
        dp = root / d
        dp.mkdir(parents=True, exist_ok=True)
        keep = dp / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
            written.append(keep)

    return written
