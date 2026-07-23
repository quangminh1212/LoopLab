"""Score how well a loop is actually engineered (0–100)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from looplab.validate import validate_spec


@dataclass
class ScoreResult:
    score: int
    band: str
    reasons: list[str]

    def summary(self) -> str:
        lines = [f"score: {self.score}/100 ({self.band})"]
        for r in self.reasons:
            lines.append(f"  - {r}")
        return "\n".join(lines)


def _band(score: int) -> str:
    if score >= 90:
        return "ready"
    if score >= 70:
        return "usable"
    if score >= 40:
        return "partial"
    return "not_loop_engineered"


def score_spec(spec: dict[str, Any]) -> ScoreResult:
    reasons: list[str] = []
    score = 0

    v = validate_spec(spec)
    if not v.ok:
        reasons.append("schema/safety validation failed")
        for e in v.errors[:5]:
            reasons.append(f"  fail: {e}")
        return ScoreResult(score=max(0, 10 - len(v.errors)), band=_band(0), reasons=reasons)

    score += 20
    reasons.append("+20 schema valid")

    # Goal + stop
    if len(str(spec.get("goal") or "")) >= 12:
        score += 8
        reasons.append("+8 concrete goal")
    else:
        reasons.append("+0 goal too vague")

    stop = spec.get("stop_conditions") or {}
    if stop.get("success_signal") and stop.get("failure_policy"):
        score += 10
        reasons.append("+10 stop conditions")
    if stop.get("stop_on_repeated_error"):
        score += 4
        reasons.append("+4 stop_on_repeated_error")

    # State
    state = spec.get("state") or {}
    if state.get("backend") != "none" and state.get("read_before_run"):
        score += 10
        reasons.append("+10 durable state")
    if state.get("update_after_run"):
        score += 4
        reasons.append("+4 state update_after_run")

    # Tools boundaries
    tools = spec.get("tools") or {}
    if tools.get("allowed") and tools.get("forbidden_actions"):
        score += 10
        reasons.append("+10 tool allow/deny")

    # Verification
    ver = spec.get("verification") or {}
    dchecks = ver.get("deterministic_checks") or []
    rchecks = ver.get("review_checks") or []
    if dchecks:
        score += 12
        reasons.append(f"+12 {len(dchecks)} deterministic check(s)")
    if rchecks:
        score += 6
        reasons.append(f"+6 {len(rchecks)} review check(s)")
    dod = ver.get("definition_of_done") or []
    if dod:
        score += 6
        reasons.append("+6 definition_of_done")

    # Receipt
    receipt = spec.get("receipt") or {}
    if receipt.get("required") and receipt.get("path"):
        score += 8
        reasons.append("+8 receipt required")

    # Isolation vs risk
    risk = spec.get("risk_class")
    isolation = (spec.get("isolation") or {}).get("mode")
    if risk in {"L0", "L1"} and isolation in {"read_only", "profile_boundary", "temp_dir"}:
        score += 6
        reasons.append("+6 isolation fits L0/L1")
    elif risk == "L2" and isolation in {"read_only", "temp_dir", "profile_boundary"}:
        score += 6
        reasons.append("+6 isolation fits L2")
    elif risk == "L3" and isolation in {"git_worktree", "git_branch", "container"}:
        score += 6
        reasons.append("+6 isolation fits L3")
    elif risk in {"L4", "L5"} and isolation not in {"none"}:
        score += 6
        reasons.append("+6 isolation set for high risk")
    else:
        reasons.append("+0 isolation/risk mismatch or weak")

    # Human gate
    human = spec.get("human_gate") or {}
    if human.get("required_for") and human.get("approval_format"):
        score += 6
        reasons.append("+6 human gate")

    score = min(100, score)
    return ScoreResult(score=score, band=_band(score), reasons=reasons)
