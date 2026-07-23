"""Run records and receipts — kit-style dry-run contract."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from looplab.io_util import dump_json, dump_yaml, load_spec
from looplab.score import score_spec
from looplab.validate import validate_spec


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_run_record(
    spec: dict[str, Any],
    *,
    spec_path: str | Path | None = None,
    mode: str = "DRY_RUN",
    min_score: int = 0,
) -> dict[str, Any]:
    v = validate_spec(spec)
    s = score_spec(spec)
    name = str(spec.get("name") or "unnamed")
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path_s = Path(spec_path).as_posix() if spec_path else "(inline)"
    status = "DRY_RUN" if v.ok and s.score >= min_score else "FAIL"
    checks = [
        {
            "name": "loop_spec_validation",
            "result": "PASS" if v.ok else "FAIL",
            "evidence": f"{path_s} schema+safety",
        },
        {
            "name": "loop_engineering_score",
            "result": str(s.score),
            "evidence": f"band={s.band}; categories={s.categories}",
        },
        {
            "name": "deterministic_checks_declared",
            "result": "PASS"
            if (_obj(spec.get("verification")).get("deterministic_checks"))
            else "FAIL",
            "evidence": f"{len(_obj(spec.get('verification')).get('deterministic_checks') or [])} check(s)",
        },
    ]
    return {
        "schema_version": "1.0",
        "loop_name": name,
        "run_id": f"dry-run-{name}-{now}",
        "goal": spec.get("goal"),
        "risk_class": spec.get("risk_class"),
        "mode": mode,
        "status": status,
        "trigger": f"dry_run_cli:{_obj(spec.get('trigger')).get('type', 'unknown')}",
        "started_at": utc_now(),
        "finished_at": utc_now(),
        "ended_at": utc_now(),
        "validation": {"ok": v.ok, "errors": v.errors, "warnings": v.warnings},
        "score": {"value": s.score, "band": s.band, "categories": s.categories, "reasons": s.reasons},
        "actions_taken": [
            "loaded loop spec",
            "validated schema and safety rules",
            "scored loop-engineering usefulness",
            "rendered dry-run receipt",
            "did not execute agent task or external side effects",
        ],
        "verification": {
            "checks": checks,
            "result": "PASS" if status == "DRY_RUN" else "FAIL",
        },
        "stop_reason": (
            "dry_run_contract_verified_no_task_execution"
            if status == "DRY_RUN"
            else "validation_or_score_failed"
        ),
        "external_side_effects": [],
        "risks": [
            "dry run does not prove live task quality",
            "run one manual read-only Hermes execution before cron/webhook",
        ],
        "receipt_path": _obj(spec.get("receipt")).get("path"),
        "cycle": spec.get("cycle") or ["observe", "plan", "act", "verify", "closeout"],
    }


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def render_receipt_md(record: dict[str, Any]) -> str:
    score = record.get("score") or {}
    ver = record.get("verification") or {}
    lines = [
        f"# Loop Run Receipt — `{record.get('loop_name')}`",
        "",
        f"- **Run ID:** `{record.get('run_id')}`",
        f"- **Status:** `{record.get('status')}`",
        f"- **Mode:** `{record.get('mode')}`",
        f"- **Risk:** `{record.get('risk_class')}`",
        f"- **Score:** {score.get('value')}/100 ({score.get('band')})",
        f"- **Verification:** `{ver.get('result')}`",
        f"- **Stop reason:** {record.get('stop_reason')}",
        f"- **Started:** {record.get('started_at')}",
        f"- **Finished:** {record.get('finished_at') or record.get('ended_at')}",
        f"- **External side effects:** {', '.join(record.get('external_side_effects') or []) or 'none'}",
        f"- **Cycle:** {', '.join(record.get('cycle') or [])}",
        "",
        "## Goal",
        "",
        str(record.get("goal") or ""),
        "",
        "## Actions taken",
        "",
    ]
    for a in record.get("actions_taken") or []:
        lines.append(f"- {a}")
    lines.extend(["", "## Validation", ""])
    val = record.get("validation") or {}
    lines.append("PASS" if val.get("ok") else "FAIL")
    for e in val.get("errors") or []:
        lines.append(f"- error: {e}")
    for w in val.get("warnings") or []:
        lines.append(f"- warn: {w}")
    risks = record.get("risks") or []
    if risks:
        lines.extend(["", "## Risks", ""])
        for r in risks:
            lines.append(f"- {r}")
    lines.append("")
    return "\n".join(lines)


def write_dry_run(
    spec_path: str | Path,
    out_dir: str | Path,
    *,
    min_score: int = 0,
) -> dict[str, Path]:
    path = Path(spec_path)
    spec = load_spec(path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    record = build_run_record(spec, spec_path=path, min_score=min_score)
    record_path = out / "run-record.yaml"
    receipt_path = out / "receipt.md"
    dump_yaml(record, record_path)
    receipt_path.write_text(render_receipt_md(record), encoding="utf-8")
    dump_json(record, out / "run-record.json")
    written = {
        "run_record": record_path,
        "receipt": receipt_path,
        "run_record_json": out / "run-record.json",
    }
    cfg_receipt = _obj(spec.get("receipt")).get("path")
    if cfg_receipt:
        p = Path(cfg_receipt)
        if not p.is_absolute():
            p = Path.cwd() / p
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(render_receipt_md(record), encoding="utf-8")
        written["configured_receipt"] = p
    return written
