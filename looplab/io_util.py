"""Load/save loop specs (YAML preferred, JSON accepted)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_spec(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"spec not found: {p}")
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
