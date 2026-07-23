"""LoopLab CLI — design, validate, score, dry-run, install Hermes skills."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from looplab import __version__
from looplab.install import default_hermes_home, install_skills
from looplab.io_util import load_spec
from looplab.receipt import render_receipt_md, write_dry_run
from looplab.score import score_spec
from looplab.templates import write_init_spec, write_project_scaffold
from looplab.validate import validate_spec


def _cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.suffix.lower() in {".yaml", ".yml", ".json"}:
        write_init_spec(path, name=args.name)
        print(f"wrote {path}")
        return 0
    written = write_project_scaffold(path)
    print(f"scaffolded project at {path}")
    for p in written:
        print(f"  + {p}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    spec = load_spec(args.spec)
    result = validate_spec(spec)
    print(result.summary())
    return 0 if result.ok else 1


def _cmd_score(args: argparse.Namespace) -> int:
    spec = load_spec(args.spec)
    result = score_spec(spec)
    print(result.summary())
    return 0 if result.score >= 40 else 2


def _cmd_dry_run(args: argparse.Namespace) -> int:
    out = Path(args.out or "runs/dry-run")
    written = write_dry_run(args.spec, out)
    print(f"dry-run written to {out}")
    for k, p in written.items():
        print(f"  {k}: {p}")
    # exit non-zero if validation failed
    spec = load_spec(args.spec)
    return 0 if validate_spec(spec).ok else 1


def _cmd_render_receipt(args: argparse.Namespace) -> int:
    record = load_spec(args.record)
    text = render_receipt_md(record)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


def _cmd_install_hermes(args: argparse.Namespace) -> int:
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    try:
        installed = install_skills(home, force=args.force)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Hermes home: {home}")
    print(f"installed/updated {len(installed)} path(s)")
    for p in installed[:20]:
        print(f"  + {p}")
    if len(installed) > 20:
        print(f"  ... +{len(installed) - 20} more")
    print("verify: hermes skills list | findstr /i looplab")
    return 0


def _cmd_smoke(args: argparse.Namespace) -> int:
    root = Path(__file__).resolve().parent.parent
    examples = list((root / "examples").rglob("loop-spec.yaml"))
    if not examples:
        print("smoke: no examples found", file=sys.stderr)
        return 1
    failed = 0
    for ex in sorted(examples):
        spec = load_spec(ex)
        v = validate_spec(spec)
        s = score_spec(spec)
        name = ex.parent.name
        # prompt-only is expected weak
        if name == "prompt-only":
            ok = not v.ok or s.score < 40
            tag = "expected-weak" if ok else "UNEXPECTED-STRONG"
            if not ok:
                failed += 1
            print(f"  [{tag}] {name}: validate={v.ok} score={s.score}")
            continue
        if not v.ok:
            failed += 1
            print(f"  [FAIL] {name}: {v.errors}")
        else:
            print(f"  [OK] {name}: score={s.score} ({s.band})")
    print(f"smoke: {len(examples)} example(s), failed={failed}")
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="looplab",
        description="LoopLab — Hermes-native loop engineering (spec → validate → score → dry-run → skills)",
    )
    p.add_argument("--version", action="version", version=f"looplab {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="Create loop-spec.yaml or scaffold a project directory")
    s.add_argument("path", help="File (.yaml) or project directory")
    s.add_argument("--name", default=None, help="Loop name when writing a single file")
    s.set_defaults(func=_cmd_init)

    s = sub.add_parser("validate", help="Validate loop contract + safety gates")
    s.add_argument("spec", help="Path to loop-spec.yaml")
    s.set_defaults(func=_cmd_validate)

    s = sub.add_parser("score", help="Score loop-engineering quality 0–100")
    s.add_argument("spec", help="Path to loop-spec.yaml")
    s.set_defaults(func=_cmd_score)

    s = sub.add_parser("dry-run", help="Contract dry-run → run-record + receipt (no Hermes execution)")
    s.add_argument("spec", help="Path to loop-spec.yaml")
    s.add_argument("--out", default=None, help="Output directory (default runs/dry-run)")
    s.set_defaults(func=_cmd_dry_run)

    s = sub.add_parser("render-receipt", help="Render markdown receipt from run-record")
    s.add_argument("record", help="Path to run-record.yaml/json")
    s.add_argument("--out", default=None, help="Write to file instead of stdout")
    s.set_defaults(func=_cmd_render_receipt)

    s = sub.add_parser("install-hermes", help="Install LoopLab skills into Hermes home")
    s.add_argument("--hermes-home", default=None, help="Override HERMES_HOME (default ~/.hermes)")
    s.add_argument("--force", action="store_true", help="Replace skill directories entirely")
    s.set_defaults(func=_cmd_install_hermes)

    s = sub.add_parser("smoke", help="Validate bundled examples")
    s.set_defaults(func=_cmd_smoke)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
