"""Load/save loop specs (YAML preferred, JSON accepted)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

# Accepted filenames when user passes a project directory instead of a file path.
_SPEC_BASENAMES = ("loop-spec.yaml", "loop-spec.yml", "loop-spec.json")


def resolve_spec_path(path: str | Path) -> Path:
    """Resolve a loop-spec file path or a project directory containing one.

    After ``looplab init <dir>``, users often pass the directory to validate/score/dry-run.
    """
    p = Path(path)
    if p.is_file():
        return p
    if p.is_dir():
        for name in _SPEC_BASENAMES:
            candidate = p / name
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(
            f"no loop-spec.yaml (or .yml/.json) in directory: {p}"
        )
    raise FileNotFoundError(f"spec not found: {p}")


def load_spec(path: str | Path) -> dict[str, Any]:
    p = resolve_spec_path(path)
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        try:
            data = yaml.safe_load(text)
        except Exception:
            data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"spec root must be a mapping: {p}")
    return data


def dump_yaml(data: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def dump_json(data: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
