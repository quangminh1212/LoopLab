"""LoopLab CLI — contract + multi-step + triage cron + OPAV."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from looplab import __version__
from looplab.cron_recipe import list_recipes, render_recipe
from looplab.cycle import CycleState, render_cycle_doc
from looplab.install import default_hermes_home, install_skills, uninstall_from_hermes
from looplab.io_util import load_spec
from looplab.privacy import format_report, scan
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
    rc = 0
    for path in args.specs:
        spec = load_spec(path)
        result = validate_spec(spec)
        print(f"== {path} ==")
        print(result.summary())
        if not result.ok:
            rc = 1
    return rc


def _cmd_score(args: argparse.Namespace) -> int:
    rc = 0
    for path in args.specs:
        spec = load_spec(path)
        result = score_spec(spec)
        print(f"== {path} ==")
        print(result.summary())
        if result.score < 40:
            rc = 2
    return rc


def _cmd_dry_run(args: argparse.Namespace) -> int:
    out = Path(args.out or "runs/dry-run")
    try:
        written = write_dry_run(args.spec, out, min_score=args.min_score)
    except Exception as e:
        print(f"FAIL dry-run: {e}", file=sys.stderr)
        return 1
    print(f"dry-run written to {out}")
    for k, p in written.items():
        print(f"  {k}: {p}")
    spec = load_spec(args.spec)
    v = validate_spec(spec)
    s = score_spec(spec)
    if not v.ok or s.score < args.min_score:
        return 1
    return 0


def _cmd_render_receipt(args: argparse.Namespace) -> int:
    record = load_spec(args.record)
    text = render_receipt_md(record)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


def _cmd_privacy_scan(args: argparse.Namespace) -> int:
    findings = scan(args.root)
    print(format_report(findings))
    return 0 if not findings else 1


def _cmd_install_hermes(args: argparse.Namespace) -> int:
    """Opt-in only — LoopLab is meant to stay outside Hermes Agent."""
    if not args.yes:
        print(
            "WARNING: LoopLab is designed to live at C:\\Dev\\LoopLab only.\n"
            "Installing into Hermes Agent home is optional and discouraged.\n"
            "Re-run with --yes to confirm, or use: looplab uninstall-hermes",
            file=sys.stderr,
        )
        return 2
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    try:
        installed = install_skills(home, force=args.force)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Hermes home: {home}")
    print(f"installed/updated {len(installed)} path(s)")
    for p in installed[:30]:
        print(f"  + {p}")
    if len(installed) > 30:
        print(f"  ... +{len(installed) - 30} more")
    print("skills: looplab (multi-step agents) + loop-triage")
    print("to remove later: looplab uninstall-hermes")
    return 0


def _cmd_uninstall_hermes(args: argparse.Namespace) -> int:
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    removed = uninstall_from_hermes(home)
    print(f"Hermes home: {home}")
    if not removed:
        print("nothing to remove (already clean)")
        return 0
    print(f"removed {len(removed)} path(s)")
    for p in removed:
        print(f"  - {p}")
    return 0


def _cmd_cron_recipe(args: argparse.Namespace) -> int:
    if args.list:
        for name in list_recipes():
            print(name)
        return 0
    try:
        print(render_recipe(args.name, workdir=args.workdir, deliver=args.deliver))
    except KeyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


def _cmd_cycle(args: argparse.Namespace) -> int:
    if args.doc:
        print(render_cycle_doc())
        return 0
    state = CycleState()
    if args.mutate:
        state.phase = state.phase.__class__("act") if False else state.phase
        from looplab.cycle import Phase

        state.phase = Phase.ACT
        state.record_mutation()
    if args.verify is not None:
        from looplab.cycle import Phase

        state.phase = Phase.VERIFY
        state.record_verification(args.verify)
    print(state.panel())
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
        if name == "prompt-only":
            ok = not v.ok or s.score < 40
            tag = "expected-weak" if ok else "UNEXPECTED-STRONG"
            if not ok:
                failed += 1
            print(f"  [{tag}] {name}: validate={v.ok} score={s.score}")
            continue
        if not v.ok:
            failed += 1
            print(f"  [FAIL] {name}: {v.errors[:3]}")
        else:
            print(f"  [OK] {name}: score={s.score} ({s.band})")
    priv = scan(root)
    # ignore findings inside patterns/opav design dump if any
    priv = [f for f in priv if "LoopCraft-DESIGN" not in f["file"]]
    if priv:
        print(f"  [WARN] privacy findings: {len(priv)}")
        for f in priv[:5]:
            print(f"    {f['file']}:{f['line']} {f['type']}")
    print(f"smoke: {len(examples)} example(s), failed={failed}")
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="looplab",
        description=(
            "LoopLab — Hermes loop engineering: "
            "contract (kit) + multi-step skill (loop-engineer) + triage/cron (cobus) + OPAV (LoopCraft)"
        ),
    )
    p.add_argument("--version", action="version", version=f"looplab {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="Create loop-spec.yaml or scaffold a project directory")
    s.add_argument("path", help="File (.yaml) or project directory")
    s.add_argument("--name", default=None, help="Loop name when writing a single file")
    s.set_defaults(func=_cmd_init)

    s = sub.add_parser("validate", help="Validate loop contract + safety gates (L0–L5)")
    s.add_argument("specs", nargs="+", help="Path(s) to loop-spec.yaml")
    s.set_defaults(func=_cmd_validate)

    s = sub.add_parser("score", help="Score loop-engineering quality 0–100")
    s.add_argument("specs", nargs="+", help="Path(s) to loop-spec.yaml")
    s.set_defaults(func=_cmd_score)

    s = sub.add_parser("dry-run", help="Contract dry-run → run-record + receipt")
    s.add_argument("spec", help="Path to loop-spec.yaml")
    s.add_argument("--out", default=None, help="Output directory (default runs/dry-run)")
    s.add_argument("--min-score", type=int, default=0, help="Minimum score to pass (default 0)")
    s.set_defaults(func=_cmd_dry_run)

    s = sub.add_parser("render-receipt", help="Render markdown receipt from run-record")
    s.add_argument("record", help="Path to run-record.yaml/json")
    s.add_argument("--out", default=None, help="Write to file instead of stdout")
    s.set_defaults(func=_cmd_render_receipt)

    s = sub.add_parser("privacy-scan", help="Scan for secrets / private paths (kit)")
    s.add_argument("root", nargs="?", default=".", help="Root path to scan")
    s.set_defaults(func=_cmd_privacy_scan)

    s = sub.add_parser(
        "install-hermes",
        help="OPT-IN: copy skills into Hermes home (discouraged; LoopLab stays external)",
    )
    s.add_argument("--hermes-home", default=None, help="Override HERMES_HOME")
    s.add_argument("--force", action="store_true", help="Replace skill directories entirely")
    s.add_argument("--yes", action="store_true", help="Confirm install into Hermes Agent")
    s.set_defaults(func=_cmd_install_hermes)

    s = sub.add_parser(
        "uninstall-hermes",
        help="Remove LoopLab skills/prefill artifacts from Hermes Agent home",
    )
    s.add_argument("--hermes-home", default=None, help="Override HERMES_HOME")
    s.set_defaults(func=_cmd_uninstall_hermes)

    s = sub.add_parser("cron-recipe", help="Print hermes cron recipe (daily-triage / briefing)")
    s.add_argument("name", nargs="?", default="daily-triage", help="Recipe name")
    s.add_argument("--list", action="store_true", help="List recipe names")
    s.add_argument("--workdir", default="$PWD")
    s.add_argument("--deliver", default=None, help="Override deliver (default local)")
    s.set_defaults(func=_cmd_cron_recipe)

    s = sub.add_parser("cycle", help="Show OPAV cycle panel (LoopCraft discipline)")
    s.add_argument("--doc", action="store_true", help="Full cycle documentation")
    s.add_argument("--mutate", action="store_true", help="Simulate a mutation")
    s.add_argument("--verify", type=lambda x: x.lower() != "false", nargs="?", const=True, default=None)
    s.set_defaults(func=_cmd_cycle)

    s = sub.add_parser("smoke", help="Validate bundled examples")
    s.set_defaults(func=_cmd_smoke)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
