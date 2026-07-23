"""Validate Hermes loop contracts — schema + kit safety rules (L0–L5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RISK_CLASSES = frozenset({"L0", "L1", "L2", "L3", "L4", "L5"})
RISK_LEVEL = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}
TRIGGER_TYPES = frozenset(
    {"manual", "cron", "webhook", "kanban", "github_issue", "file_change", "other"}
)
STATE_BACKENDS = frozenset({"none", "file", "kanban", "github_issue", "database", "receipt"})
ISOLATION_MODES = frozenset(
    {"read_only", "temp_dir", "git_branch", "git_worktree", "profile_boundary", "container", "none"}
)
REAL_ISOLATION_L3 = frozenset({"git_worktree", "temp_dir", "container", "profile_boundary", "git_branch"})

DANGER_ALIASES = {
    "deletion": {"deletion", "delete_files", "delete_data"},
    "secrets": {"secrets", "access_secrets", "print_secrets"},
    "public_posting": {"public_posting", "send_messages", "post_publicly"},
    "production_deploy": {"production_deploy", "deploy_production", "restart_services"},
    "payments": {"payments", "billing", "purchase"},
}

REQUIRED_TOP = (
    "schema_version",
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
)


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        lines = [f"validate: {status}"]
        for e in self.errors:
            lines.append(f"  error: {e}")
        for w in self.warnings:
            lines.append(f"  warn:  {w}")
        return "\n".join(lines)


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _missing_danger_coverage(values: set[str]) -> list[str]:
    return sorted(name for name, aliases in DANGER_ALIASES.items() if not (values & aliases))


def _req_keys(obj: Any, keys: tuple[str, ...], path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{path} must be an object")
        return
    for k in keys:
        if k not in obj:
            errors.append(f"{path}.{k} is required")


def safety_rules(spec: dict[str, Any]) -> list[str]:
    """Kit-style operational safety rules beyond pure schema."""
    errors: list[str] = []
    risk_class = spec.get("risk_class")
    lvl = RISK_LEVEL.get(risk_class if isinstance(risk_class, str) else "", -1)
    stop = _obj(spec.get("stop_conditions"))
    if not stop.get("success_signal"):
        errors.append("missing stop_conditions.success_signal")
    if not stop.get("failure_policy"):
        errors.append("missing stop_conditions.failure_policy")
    try:
        mi = int(stop.get("max_iterations") or 0)
        if mi > 3 and lvl >= 1 and not stop.get("rationale"):
            errors.append("max_iterations above 3 needs stop_conditions.rationale")
    except (TypeError, ValueError):
        pass

    verification = _obj(spec.get("verification"))
    if not (verification.get("deterministic_checks") or verification.get("review_checks")):
        errors.append("missing verification checks")
    if lvl >= 3 and not verification.get("deterministic_checks"):
        errors.append("L3+ requires deterministic verification")

    isolation_mode = _obj(spec.get("isolation")).get("mode")
    if lvl >= 3 and isolation_mode not in REAL_ISOLATION_L3:
        errors.append("L3+ requires real isolation (git_worktree|temp_dir|container|profile_boundary|git_branch)")

    tools = _obj(spec.get("tools"))
    gates = _obj(spec.get("human_gate"))
    forbidden = set(tools.get("forbidden_actions") or [])
    required_for = set(gates.get("required_for") or [])
    missing_forbidden = _missing_danger_coverage(forbidden)
    missing_gates = _missing_danger_coverage(required_for)
    if missing_forbidden:
        errors.append("forbidden_actions missing dangerous actions: " + ", ".join(missing_forbidden))
    if missing_gates:
        errors.append("human gates missing dangerous actions: " + ", ".join(missing_gates))

    if _obj(spec.get("receipt")).get("required") is not True:
        errors.append("receipt.required must be true")
    if _obj(spec.get("trigger")).get("type") == "cron" and lvl >= 3:
        errors.append("cron-triggered L3+ blocked by default")
    return errors


def validate_spec(spec: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in spec:
            errors.append(f"missing required field: {k}")
    if errors:
        return ValidationResult(ok=False, errors=errors)

    if not str(spec.get("name") or "").strip():
        errors.append("name must be non-empty")
    if not str(spec.get("goal") or "").strip():
        errors.append("goal must be non-empty")

    risk = spec.get("risk_class")
    if risk not in RISK_CLASSES:
        errors.append(f"risk_class must be one of {sorted(RISK_CLASSES)}")

    trigger = _obj(spec.get("trigger"))
    _req_keys(trigger, ("type",), "trigger", errors)
    ttype = trigger.get("type")
    if ttype not in TRIGGER_TYPES:
        errors.append(f"trigger.type must be one of {sorted(TRIGGER_TYPES)}")
    if ttype == "cron" and not trigger.get("schedule"):
        errors.append("trigger.schedule required when trigger.type=cron")

    inputs = _obj(spec.get("inputs"))
    _req_keys(inputs, ("required",), "inputs", errors)
    if "required" in inputs and not isinstance(inputs.get("required"), list):
        errors.append("inputs.required must be an array")

    state = _obj(spec.get("state"))
    _req_keys(state, ("backend", "location", "read_before_run"), "state", errors)
    if state.get("backend") not in STATE_BACKENDS:
        errors.append(f"state.backend must be one of {sorted(STATE_BACKENDS)}")
    if state.get("backend") != "none" and not str(state.get("location") or "").strip():
        errors.append("state.location required when backend != none")

    tools = _obj(spec.get("tools"))
    _req_keys(tools, ("allowed", "forbidden_actions"), "tools", errors)
    if not isinstance(tools.get("forbidden_actions"), list) or len(tools.get("forbidden_actions") or []) < 1:
        errors.append("tools.forbidden_actions must be a non-empty array")
    if not isinstance(tools.get("allowed"), list):
        errors.append("tools.allowed must be an array")

    isolation = _obj(spec.get("isolation"))
    _req_keys(isolation, ("mode",), "isolation", errors)
    if isolation.get("mode") not in ISOLATION_MODES:
        errors.append(f"isolation.mode must be one of {sorted(ISOLATION_MODES)}")

    verification = _obj(spec.get("verification"))
    _req_keys(verification, ("deterministic_checks", "review_checks"), "verification", errors)
    dchecks = verification.get("deterministic_checks")
    if not isinstance(dchecks, list):
        errors.append("verification.deterministic_checks must be an array")
    else:
        for i, c in enumerate(dchecks):
            if not isinstance(c, dict):
                errors.append(f"verification.deterministic_checks[{i}] must be object")
                continue
            for key in ("name", "method", "pass_condition"):
                if not str(c.get(key) or "").strip():
                    errors.append(f"verification.deterministic_checks[{i}].{key} required")
    if not isinstance(verification.get("review_checks"), list):
        errors.append("verification.review_checks must be an array")

    stop = _obj(spec.get("stop_conditions"))
    _req_keys(
        stop,
        ("max_iterations", "max_runtime_minutes", "success_signal", "failure_policy"),
        "stop_conditions",
        errors,
    )
    try:
        mi = int(stop.get("max_iterations"))
        if not 1 <= mi <= 50:
            errors.append("stop_conditions.max_iterations must be 1..50")
    except (TypeError, ValueError):
        errors.append("stop_conditions.max_iterations must be int")
    try:
        rt = int(stop.get("max_runtime_minutes"))
        if not 1 <= rt <= 1440:
            errors.append("stop_conditions.max_runtime_minutes must be 1..1440")
    except (TypeError, ValueError):
        errors.append("stop_conditions.max_runtime_minutes must be int")

    human = _obj(spec.get("human_gate"))
    _req_keys(human, ("required_for", "approval_format"), "human_gate", errors)
    if not isinstance(human.get("required_for"), list) or len(human.get("required_for") or []) < 1:
        errors.append("human_gate.required_for must be a non-empty array")

    outputs = _obj(spec.get("outputs"))
    _req_keys(outputs, ("artifacts",), "outputs", errors)
    if not isinstance(outputs.get("artifacts"), list):
        errors.append("outputs.artifacts must be an array")

    receipt = _obj(spec.get("receipt"))
    _req_keys(receipt, ("required", "path"), "receipt", errors)
    if receipt.get("required") is True and not str(receipt.get("path") or "").strip():
        errors.append("receipt.path required when receipt.required=true")

    # OPAV cycle advisory
    cycle = spec.get("cycle")
    if not cycle:
        warnings.append("missing cycle[] — recommend observe/plan/act/verify/closeout")

    # Kit safety rules
    errors.extend(safety_rules(spec))

    # de-dupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for e in errors:
        if e not in seen:
            seen.add(e)
            uniq.append(e)

    return ValidationResult(ok=len(uniq) == 0, errors=uniq, warnings=warnings)
