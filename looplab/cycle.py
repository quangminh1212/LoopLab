"""Loop cycles — multi-profile (OPAV / hermes-coding / kit).

Profiles map equivalent GitHub loop methodologies into one durable panel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class Phase(str, Enum):
    """OPAV phases (default profile)."""

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

# Multi-source cycle profiles (equivalent GitHub methodologies)
CYCLE_PROFILES: dict[str, dict[str, Any]] = {
    "opav": {
        "title": "OPAV (LoopCraft / proofrail)",
        "source": "https://github.com/410979729/proofrail-hermes",
        "phases": ["observe", "plan", "act", "verify", "closeout"],
        "hints": {p.value: PHASE_HINTS[p] for p in ORDER},
        "mutate_phase": "act",
        "verify_phase": "verify",
    },
    "hermes-coding": {
        "title": "Hermes Coding 4-phase",
        "source": "https://github.com/douglas-ou/hermes-coding",
        "phases": ["clarify", "breakdown", "implement", "deliver"],
        "hints": {
            "clarify": "Structured Q&A → PRD / requirements. No code yet.",
            "breakdown": "Split PRD into atomic tasks with dependencies.",
            "implement": "One task at a time; tests first; self-heal on failure.",
            "deliver": "Quality gates (lint/type/test) then commit/PR.",
        },
        "mutate_phase": "implement",
        "verify_phase": "deliver",
    },
    "kit": {
        "title": "Agent loop engineering kit",
        "source": "https://github.com/AlekseiUL/agent-loop-engineering-kit",
        "phases": ["design", "validate", "dry_run", "execute", "audit"],
        "hints": {
            "design": "Write loop-spec contract (L0–L5 safety gates).",
            "validate": "Run looplab validate + score before automation.",
            "dry_run": "Contract dry-run → run-record + receipt (no live side effects).",
            "execute": "Live loop under isolation / worktree rules.",
            "audit": "Privacy scan + receipt completeness + stop_reason.",
        },
        "mutate_phase": "execute",
        "verify_phase": "audit",
    },
}


def list_profiles() -> list[str]:
    return sorted(CYCLE_PROFILES.keys())


def get_profile(name: str | None) -> dict[str, Any]:
    key = (name or "opav").strip().lower()
    if key not in CYCLE_PROFILES:
        raise KeyError(f"unknown cycle profile {name!r}; choose from {', '.join(list_profiles())}")
    return CYCLE_PROFILES[key]


@dataclass
class CycleState:
    profile: str = "opav"
    phase: str = "observe"
    pending_verification: bool = False
    mutations: int = 0
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Accept Phase enum for backward compatibility
        if isinstance(self.phase, Phase):
            self.phase = self.phase.value
        if self.profile not in CYCLE_PROFILES:
            self.profile = "opav"
        phases = self.order()
        if self.phase not in phases:
            self.phase = phases[0]

    def order(self) -> list[str]:
        return list(get_profile(self.profile)["phases"])

    def hints(self) -> dict[str, str]:
        return dict(get_profile(self.profile).get("hints") or {})

    def advance(self) -> str:
        order = self.order()
        try:
            idx = order.index(self.phase)
        except ValueError:
            idx = 0
            self.phase = order[0]
        if idx >= len(order) - 1:
            return self.phase
        self.phase = order[idx + 1]
        return self.phase

    def record_mutation(self) -> None:
        meta = get_profile(self.profile)
        self.phase = str(meta.get("mutate_phase") or self.phase)
        self.mutations += 1
        self.pending_verification = True
        self.notes.append(f"mutation#{self.mutations} → pending_verification")

    def record_verification(self, ok: bool) -> None:
        meta = get_profile(self.profile)
        self.pending_verification = False
        self.notes.append(f"verify={'PASS' if ok else 'FAIL'}")
        vphase = str(meta.get("verify_phase") or "verify")
        mphase = str(meta.get("mutate_phase") or "act")
        if ok and self.phase == mphase:
            self.phase = vphase

    def panel(self) -> str:
        meta = get_profile(self.profile)
        hints = self.hints()
        lines = [
            f"# LoopLab cycle panel ({self.profile})",
            f"- profile: **{self.profile}** — {meta.get('title')}",
            f"- source: {meta.get('source')}",
            f"- phase: **{self.phase}**",
            f"- pending_verification: {self.pending_verification}",
            f"- mutations: {self.mutations}",
            "",
            "## Cycle",
        ]
        for p in self.order():
            mark = "→" if p == self.phase else " "
            lines.append(f"{mark} {p}: {hints.get(p, '')}")
        if self.notes:
            lines.extend(["", "## Notes", *[f"- {n}" for n in self.notes[-8:]]])
        return "\n".join(lines)


def cycle_from_spec(spec: dict[str, Any] | None = None) -> list[str]:
    if spec and isinstance(spec.get("cycle"), list) and spec["cycle"]:
        return [str(x) for x in spec["cycle"]]
    return [p.value for p in ORDER]


def render_cycle_doc() -> str:
    lines = [
        "# LoopLab cycle profiles (equivalent GitHub methodologies)",
        "",
    ]
    for key, meta in CYCLE_PROFILES.items():
        lines.append(f"## {key} — {meta.get('title')}")
        lines.append(f"Source: {meta.get('source')}")
        lines.append("")
        hints = meta.get("hints") or {}
        for p in meta.get("phases") or []:
            lines.append(f"- **{p}**: {hints.get(p, '')}")
        lines.append("")
    lines.extend(
        [
            "## Defaults",
            "- enforcement: advisory unless risk ≥ L4",
            "- after mutation: verify before next mutation batch",
            "- receipt required on closeout / deliver / audit",
            "",
        ]
    )
    return "\n".join(lines)


def cycle_state_path(project_dir: str | Path) -> Path:
    return Path(project_dir) / "state" / "opav-cycle.yaml"


def load_cycle_state(project_dir: str | Path) -> CycleState:
    path = cycle_state_path(project_dir)
    if not path.is_file():
        return CycleState()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return CycleState()
    if not isinstance(data, dict):
        return CycleState()
    profile = str(data.get("profile") or "opav").lower()
    if profile not in CYCLE_PROFILES:
        profile = "opav"
    phase_raw = str(data.get("phase") or get_profile(profile)["phases"][0]).lower()
    notes = data.get("notes") or []
    if not isinstance(notes, list):
        notes = []
    return CycleState(
        profile=profile,
        phase=phase_raw,
        pending_verification=bool(data.get("pending_verification")),
        mutations=int(data.get("mutations") or 0),
        notes=[str(n) for n in notes],
    )


def save_cycle_state(project_dir: str | Path, state: CycleState) -> Path:
    path = cycle_state_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profile": state.profile,
        "phase": state.phase if isinstance(state.phase, str) else getattr(state.phase, "value", str(state.phase)),
        "pending_verification": state.pending_verification,
        "mutations": state.mutations,
        "notes": list(state.notes[-32:]),
    }
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path
