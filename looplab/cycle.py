"""OPAV cycle — observe → plan → act → verify → closeout (LoopCraft-inspired)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class Phase(str, Enum):
    OBSERVE = "observe"
    PLAN = "plan"
    ACT = "act"
    VERIFY = "verify"
    CLOSEOUT = "closeout"


ORDER: tuple[Phase, ...] = (
    Phase.OBSERVE,
    Phase.PLAN,
    Phase.ACT,
    Phase.VERIFY,
    Phase.CLOSEOUT,
)

PHASE_HINTS: dict[Phase, str] = {
    Phase.OBSERVE: "Read loop-spec, STATE.md, repo signals, prior receipts. No mutations.",
    Phase.PLAN: "List atomic steps, risk class, isolation, verification, stop conditions.",
    Phase.ACT: "Smallest safe action. Respect forbidden_actions. Prefer worktree for L3+.",
    Phase.VERIFY: "Run deterministic checks before claiming success. No more mutation if pending verify.",
    Phase.CLOSEOUT: "Update STATE.md, write receipt with stop_reason, list side effects.",
}


@dataclass
class CycleState:
    phase: Phase = Phase.OBSERVE
    pending_verification: bool = False
    mutations: int = 0
    notes: list[str] = field(default_factory=list)

    def advance(self) -> Phase:
        idx = ORDER.index(self.phase)
        if idx >= len(ORDER) - 1:
            return self.phase
        self.phase = ORDER[idx + 1]
        return self.phase

    def record_mutation(self) -> None:
        self.mutations += 1
        self.pending_verification = True
        self.notes.append(f"mutation#{self.mutations} → pending_verification")

    def record_verification(self, ok: bool) -> None:
        self.pending_verification = False
        self.notes.append(f"verify={'PASS' if ok else 'FAIL'}")
        if ok and self.phase == Phase.ACT:
            self.phase = Phase.VERIFY

    def panel(self) -> str:
        lines = [
            "# LoopLab OPAV panel",
            f"- phase: **{self.phase.value}**",
            f"- pending_verification: {self.pending_verification}",
            f"- mutations: {self.mutations}",
            "",
            "## Cycle",
        ]
        for p in ORDER:
            mark = "→" if p == self.phase else " "
            lines.append(f"{mark} {p.value}: {PHASE_HINTS[p]}")
        if self.notes:
            lines.extend(["", "## Notes", *[f"- {n}" for n in self.notes[-8:]]])
        return "\n".join(lines)


def cycle_from_spec(spec: dict[str, Any] | None = None) -> list[str]:
    if spec and isinstance(spec.get("cycle"), list) and spec["cycle"]:
        return [str(x) for x in spec["cycle"]]
    return [p.value for p in ORDER]


def render_cycle_doc() -> str:
    lines = [
        "# LoopLab OPAV (from LoopCraft / proofrail discipline)",
        "",
        "Every loop unit of work walks this cycle. The agent must not skip VERIFY or CLOSEOUT.",
        "",
    ]
    for p in ORDER:
        lines.append(f"## {p.value}")
        lines.append(PHASE_HINTS[p])
        lines.append("")
    lines.extend(
        [
            "## Defaults",
            "- enforcement: advisory (guide, don't hard-block) unless risk ≥ L4",
            "- after mutation: verify before next mutation batch",
            "- receipt required on closeout",
            "",
        ]
    )
    return "\n".join(lines)


def cycle_state_path(project_dir: str | Path) -> Path:
    return Path(project_dir) / "state" / "opav-cycle.yaml"


def load_cycle_state(project_dir: str | Path) -> CycleState:
    """Load durable OPAV panel from project ``state/opav-cycle.yaml`` if present."""
    path = cycle_state_path(project_dir)
    if not path.is_file():
        return CycleState()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return CycleState()
    if not isinstance(data, dict):
        return CycleState()
    phase_raw = str(data.get("phase") or "observe").lower()
    try:
        phase = Phase(phase_raw)
    except ValueError:
        phase = Phase.OBSERVE
    notes = data.get("notes") or []
    if not isinstance(notes, list):
        notes = []
    return CycleState(
        phase=phase,
        pending_verification=bool(data.get("pending_verification")),
        mutations=int(data.get("mutations") or 0),
        notes=[str(n) for n in notes],
    )


def save_cycle_state(project_dir: str | Path, state: CycleState) -> Path:
    path = cycle_state_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": state.phase.value,
        "pending_verification": state.pending_verification,
        "mutations": state.mutations,
        "notes": list(state.notes[-32:]),
    }
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path
