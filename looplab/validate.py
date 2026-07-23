"""Validate Hermes loop contracts (LoopLab schema v1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RISK_CLASSES = frozenset({"L0", "L1", "L2", "L3", "L4", "L5"})
TRIGGER_TYPES = frozenset(
    {"manual", "cron", "webhook", "kanban", "github_issue", "file_change", "other"}
)
STATE_BACKENDS = frozenset({"none", "file", "kanban", "github_issue", "database", "receipt"})
ISOLATION_MODES = frozenset(
    {"read_only", "temp_dir", "git_branch", "git_worktree", "profile_boundary", "container", "none"}
)

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

HIGH_RISK = frozenset({"L3", "L4", "L5"})
WRITE_RISKY = frozenset({"L4", "L5"})


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


def _req_keys(obj: Any, keys: tuple[str, ...], path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{path} must be an object")
        return
    for k in keys:
        if k not in obj:
            errors.append(f"{path}.{k} is required")


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

    trigger = spec.get("trigger") or {}
    _req_keys(trigger, ("type",), "trigger", errors)
    if isinstance(trigger, dict):
        ttype = trigger.get("type")
        if ttype not in TRIGGER_TYPES:
            errors.append(f"trigger.type must be one of {sorted(TRIGGER_TYPES)}")
        if ttype == "cron" and not trigger.get("schedule"):
            errors.append("trigger.schedule required when trigger.type=cron")

    inputs = spec.get("inputs") or {}
    _req_keys(inputs, ("required",), "inputs", errors)
    if isinstance(inputs, dict) and not isinstance(inputs.get("required"), list):
        errors.append("inputs.required must be an array")

    state = spec.get("state") or {}
    _req_keys(state, ("backend", "location", "read_before_run"), "state", errors)
    if isinstance(state, dict):
        if state.get("backend") not in STATE_BACKENDS:
            errors.append(f"state.backend must be one of {sorted(STATE_BACKENDS)}")
        if state.get("backend") != "none" and not str(state.get("location") or "").strip():
            errors.append("state.location required when backend != none")

    tools = spec.get("tools") or {}
    _req_keys(tools, ("allowed", "forbidden_actions"), "tools", errors)
    if isinstance(tools, dict):
        forbidden = tools.get("forbidden_actions")
        if not isinstance(forbidden, list) or len(forbidden) < 1:
            errors.append("tools.forbidden_actions must be a non-empty array")
        allowed = tools.get("allowed")
        if not isinstance(allowed, list):
            errors.append("tools.allowed must be an array")

    isolation = spec.get("isolation") or {}
    _req_keys(isolation, ("mode",), "isolation", errors)
    if isinstance(isolation, dict) and isolation.get("mode") not in ISOLATION_MODES:
        errors.append(f"isolation.mode must be one of {sorted(ISOLATION_MODES)}")

    verification = spec.get("verification") or {}
    _req_keys(verification, ("deterministic_checks", "review_checks"), "verification", errors)
    if isinstance(verification, dict):
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
        rchecks = verification.get("review_checks")
        if not isinstance(rchecks, list):
            errors.append("verification.review_checks must be an array")

    stop = spec.get("stop_conditions") or {}
    _req_keys(
        stop,
        ("max_iterations", "max_runtime_minutes", "success_signal", "failure_policy"),
        "stop_conditions",
        errors,
    )
    if isinstance(stop, dict):
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

    human = spec.get("human_gate") or {}
    _req_keys(human, ("required_for", "approval_format"), "human_gate", errors)
    if isinstance(human, dict):
        rf = human.get("required_for")
        if not isinstance(rf, list) or len(rf) < 1:
            errors.append("human_gate.required_for must be a non-empty array")

    outputs = spec.get("outputs") or {}
    _req_keys(outputs, ("artifacts",), "outputs", errors)
    if isinstance(outputs, dict) and not isinstance(outputs.get("artifacts"), list):
        errors.append("outputs.artifacts must be an array")

    receipt = spec.get("receipt") or {}
    _req_keys(receipt, ("required", "path"), "receipt", errors)
    if isinstance(receipt, dict) and receipt.get("required") is True:
        if not str(receipt.get("path") or "").strip():
            errors.append("receipt.path required when receipt.required=true")

    # Safety gates (policy, not pure schema)
    if risk in HIGH_RISK and isinstance(isolation, dict):
        mode = isolation.get("mode")
        if mode in {"none", "read_only"} and risk == "L3":
            warnings.append("L3 file edits should use git_worktree or git_branch isolation")
        if risk in WRITE_RISKY and mode == "none":
            errors.append(f"{risk} requires isolation.mode != none")

    if risk in HIGH_RISK and isinstance(verification, dict):
        dchecks = verification.get("deterministic_checks") or []
        if isinstance(dchecks, list) and len(dchecks) == 0:
            errors.append(f"{risk} requires at least one deterministic_checks entry")

    if isinstance(trigger, dict) and trigger.get("type") == "cron" and risk in WRITE_RISKY:
        if isinstance(human, dict):
            rf = human.get("required_for") or []
            if "unattended_write" not in rf and "production_deploy" not in rf:
                warnings.append(
                    "cron + L4/L5 should list unattended_write or production_deploy in human_gate"
                )

    return ValidationResult(ok=len(errors) == 0, errors=errors, warnings=warnings)
