"""Score loop-engineering usefulness — kit category weights (0–100)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from looplab.validate import DANGER_ALIASES, validate_spec

WEIGHTS = {
    "contract": 20,
    "safety": 20,
    "verification": 20,
    "observability": 15,
    "hermes_fit": 15,
    "operability": 10,
}

HERMES_TRIGGERS = {"manual", "cron", "webhook", "kanban", "github_issue", "file_change"}
HERMES_STATE = {"file", "kanban", "github_issue", "database", "receipt"}
REAL_ISOLATION = {
    "read_only",
    "temp_dir",
    "git_branch",
    "git_worktree",
    "profile_boundary",
    "container",
}


@dataclass
class ScoreResult:
    score: int
    band: str
    categories: dict[str, int]
    reasons: list[str]

    def summary(self) -> str:
        lines = [f"score: {self.score}/100 ({self.band})"]
        cats = ", ".join(f"{k}={v}" for k, v in self.categories.items())
        lines.append(f"  categories: {cats}")
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


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _covers_dangers(values: set[str]) -> bool:
    return all(values & aliases for aliases in DANGER_ALIASES.values())


def score_spec(spec: dict[str, Any]) -> ScoreResult:
    findings: list[str] = []
    scores = {key: 0 for key in WEIGHTS}

    v = validate_spec(spec)
    if not v.ok:
        findings.append("schema/safety validation failed")
        for e in v.errors[:6]:
            findings.append(f"  fail: {e}")
        # still score partial signal for weak specs
        base = max(0, 15 - 2 * len(v.errors))
        return ScoreResult(
            score=base,
            band=_band(base),
            categories=scores,
            reasons=findings,
        )

    required_top = [
        "name",
        "goal",
        "risk_class",
        "trigger",
        "inputs",
        "state",
        "tools",
        "isolation",
        "verification",
        "stop_conditions",
        "human_gate",
        "outputs",
        "receipt",
    ]
    present = sum(1 for key in required_top if key in spec and spec.get(key) not in (None, "", [], {}))
    scores["contract"] += round(12 * present / len(required_top))
    if spec.get("schema_version"):
        scores["contract"] += 2
    if isinstance(spec.get("goal"), str) and len(spec["goal"].strip()) >= 20:
        scores["contract"] += 3
    if spec.get("risk_class") in {"L0", "L1", "L2", "L3", "L4", "L5"}:
        scores["contract"] += 3
    scores["contract"] = min(WEIGHTS["contract"], scores["contract"])
    findings.append(f"+contract {scores['contract']}/{WEIGHTS['contract']}")

    tools = _obj(spec.get("tools"))
    gates = _obj(spec.get("human_gate"))
    isolation = _obj(spec.get("isolation"))
    forbidden = set(tools.get("forbidden_actions") or [])
    required_for = set(gates.get("required_for") or [])
    risk_class = spec.get("risk_class", "L0")
    risk_level = int(str(risk_class)[1]) if isinstance(risk_class, str) and str(risk_class)[1:].isdigit() else 0

    if _covers_dangers(forbidden):
        scores["safety"] += 7
    else:
        findings.append("safety: forbidden_actions incomplete danger coverage")
    if _covers_dangers(required_for):
        scores["safety"] += 7
    else:
        findings.append("safety: human_gate incomplete danger coverage")
    mode = isolation.get("mode")
    if mode in REAL_ISOLATION:
        scores["safety"] += 4
    if risk_level >= 3 and mode in {"git_worktree", "container", "temp_dir"}:
        scores["safety"] += 2
    scores["safety"] = min(WEIGHTS["safety"], scores["safety"])
    findings.append(f"+safety {scores['safety']}/{WEIGHTS['safety']}")

    ver = _obj(spec.get("verification"))
    dchecks = ver.get("deterministic_checks") or []
    rchecks = ver.get("review_checks") or []
    dod = ver.get("definition_of_done") or []
    if dchecks:
        scores["verification"] += min(12, 4 + 2 * min(len(dchecks), 4))
    if rchecks:
        scores["verification"] += 4
    if dod:
        scores["verification"] += 4
    scores["verification"] = min(WEIGHTS["verification"], scores["verification"])
    findings.append(f"+verification {scores['verification']}/{WEIGHTS['verification']}")

    state = _obj(spec.get("state"))
    receipt = _obj(spec.get("receipt"))
    if state.get("backend") in HERMES_STATE and state.get("read_before_run"):
        scores["observability"] += 6
    if state.get("update_after_run"):
        scores["observability"] += 3
    if receipt.get("required") and receipt.get("path"):
        scores["observability"] += 6
    scores["observability"] = min(WEIGHTS["observability"], scores["observability"])
    findings.append(f"+observability {scores['observability']}/{WEIGHTS['observability']}")

    trigger = _obj(spec.get("trigger"))
    if trigger.get("type") in HERMES_TRIGGERS:
        scores["hermes_fit"] += 5
    hermes = _obj(spec.get("hermes"))
    if hermes.get("skill") or hermes.get("deliver"):
        scores["hermes_fit"] += 5
    if hermes.get("delegate") or hermes.get("cron_prompt"):
        scores["hermes_fit"] += 3
    cycle = spec.get("cycle") or []
    if isinstance(cycle, list) and {"observe", "plan", "act", "verify", "closeout"}.issubset(set(cycle)):
        scores["hermes_fit"] += 2
    scores["hermes_fit"] = min(WEIGHTS["hermes_fit"], scores["hermes_fit"])
    findings.append(f"+hermes_fit {scores['hermes_fit']}/{WEIGHTS['hermes_fit']}")

    stop = _obj(spec.get("stop_conditions"))
    if stop.get("success_signal") and stop.get("failure_policy"):
        scores["operability"] += 4
    if stop.get("stop_on_repeated_error"):
        scores["operability"] += 3
    try:
        if 1 <= int(stop.get("max_iterations", 0)) <= 10:
            scores["operability"] += 3
    except (TypeError, ValueError):
        pass
    scores["operability"] = min(WEIGHTS["operability"], scores["operability"])
    findings.append(f"+operability {scores['operability']}/{WEIGHTS['operability']}")

    total = min(100, sum(scores.values()))
    return ScoreResult(score=total, band=_band(total), categories=scores, reasons=findings)
