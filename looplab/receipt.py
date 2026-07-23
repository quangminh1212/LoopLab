"""Run records and human-readable receipts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from looplab.io_util import dump_json, dump_yaml, load_spec
from looplab.score import score_spec
from looplab.validate import validate_spec


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_run_record(
    spec: dict[str, Any],
    *,
    mode: str = "DRY_RUN",
    status: str = "PASS",
    stop_reason: str = "contract dry run completed",
    notes: str = "",
    side_effects: list[str] | None = None,
) -> dict[str, Any]:
    v = validate_spec(spec)
    s = score_spec(spec)
    return {
        "schema_version": "1.0",
        "loop_name": spec.get("name"),
        "goal": spec.get("goal"),
        "risk_class": spec.get("risk_class"),
        "mode": mode,
        "status": status if v.ok else "FAIL",
        "started_at": utc_now(),
        "finished_at": utc_now(),
        "validation": {
            "ok": v.ok,
            "errors": v.errors,
            "warnings": v.warnings,
        },
        "score": {"value": s.score, "band": s.band, "reasons": s.reasons},
        "verification": {
            "deterministic_checks": (spec.get("verification") or {}).get("deterministic_checks", []),
            "result": "PASS" if v.ok else "FAIL",
        },
        "stop_reason": stop_reason if v.ok else "validation failed",
        "external_side_effects": side_effects or [],
        "notes": notes,
        "receipt_path": (spec.get("receipt") or {}).get("path"),
    }


def render_receipt_md(record: dict[str, Any]) -> str:
    lines = [
        f"# Loop Run Receipt — `{record.get('loop_name')}`",
        "",
        f"- **Status:** `{record.get('status')}`",
        f"- **Mode:** `{record.get('mode')}`",
        f"- **Risk:** `{record.get('risk_class')}`",
        f"- **Score:** {((record.get('score') or {}).get('value'))}/100 "
        f"({(record.get('score') or {}).get('band')})",
        f"- **Verification:** `{(record.get('verification') or {}).get('result')}`",
        f"- **Stop reason:** {record.get('stop_reason')}",
        f"- **Started:** {record.get('started_at')}",
        f"- **Finished:** {record.get('finished_at')}",
        f"- **External side effects:** {', '.join(record.get('external_side_effects') or []) or 'none'}",
        "",
        "## Goal",
        "",
        str(record.get("goal") or ""),
        "",
        "## Validation",
        "",
    ]
    val = record.get("validation") or {}
    if val.get("ok"):
        lines.append("PASS")
    else:
        lines.append("FAIL")
        for e in val.get("errors") or []:
            lines.append(f"- error: {e}")
    warns = val.get("warnings") or []
    if warns:
        lines.append("")
        lines.append("### Warnings")
        for w in warns:
            lines.append(f"- {w}")
    notes = record.get("notes")
    if notes:
        lines.extend(["", "## Notes", "", str(notes)])
    lines.append("")
    return "\n".join(lines)


def write_dry_run(spec_path: str | Path, out_dir: str | Path) -> dict[str, Path]:
    spec = load_spec(spec_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    record = build_run_record(spec)
    record_path = out / "run-record.yaml"
    receipt_path = out / "receipt.md"
    dump_yaml(record, record_path)
    receipt_path.write_text(render_receipt_md(record), encoding="utf-8")
    dump_json(record, out / "run-record.json")
    # Also write configured receipt path if relative and under out is not forced
    cfg_receipt = (spec.get("receipt") or {}).get("path")
    written = {
        "run_record": record_path,
        "receipt": receipt_path,
        "run_record_json": out / "run-record.json",
    }
    if cfg_receipt:
        p = Path(cfg_receipt)
        if not p.is_absolute():
            p = Path.cwd() / p
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(render_receipt_md(record), encoding="utf-8")
        written["configured_receipt"] = p
    return written
