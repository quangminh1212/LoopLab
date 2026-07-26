"""LoopLab CLI — contract + multi-step + triage cron + OPAV + Hermes attach."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from looplab import __version__
from looplab.cron_recipe import list_recipes, render_recipe
from looplab.cycle import CycleState, render_cycle_doc
from looplab.install import attach_to_hermes, default_hermes_home, uninstall_from_hermes
from looplab.io_util import load_spec
from looplab.privacy import format_report, scan
from looplab.receipt import render_receipt_md, write_dry_run
from looplab.score import score_spec
from looplab.templates import write_init_spec, write_project_scaffold
from looplab.validate import validate_spec


def _ensure_utf8_stdio() -> None:
    """Avoid UnicodeEncodeError on Windows consoles using cp1252."""
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            try:
                reconf(encoding="utf-8", errors="replace")
            except Exception:
                pass


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


def _cmd_attach(args: argparse.Namespace) -> int:
    """Attach skills into Hermes via junctions — no hermes-agent source edits."""
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    try:
        linked = attach_to_hermes(home, install_cli=not args.no_cli)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Hermes home: {home}")
    print(f"attached {len(linked)} path(s) (junction/symlink + optional CLI, SoT = LoopLab repo)")
    for p in linked:
        print(f"  + {p}")
    print("Hermes can use /looplab (modes: build|research|patch|audit|triage) without code changes.")
    print("CLI available as: python -m looplab (Hermes agent venv when present).")
    print("Detach: looplab detach   or   scripts\\uninstall.ps1")
    return 0


def _cmd_detach(args: argparse.Namespace) -> int:
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    removed = uninstall_from_hermes(home)
    print(f"Hermes home: {home}")
    if not removed:
        print("nothing to remove (already clean)")
        return 0
    print(f"detached {len(removed)} path(s)")
    for p in removed:
        print(f"  - {p}")
    return 0


# aliases used in older docs
def _cmd_install_hermes(args: argparse.Namespace) -> int:
    return _cmd_attach(args)


def _cmd_uninstall_hermes(args: argparse.Namespace) -> int:
    return _cmd_detach(args)


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


def _cmd_sources(args: argparse.Namespace) -> int:
    from looplab.sources import (
        check_catalog,
        format_catalog,
        write_ai_agent_index_from_powerup,
    )

    if getattr(args, "refresh_powerup", None):
        from pathlib import Path as _P

        root = _P(args.refresh_powerup)
        if not root.is_dir():
            print(f"error: AI_PowerUp path not found: {root}", file=sys.stderr)
            return 1
        dest, n = write_ai_agent_index_from_powerup(root)
        print(f"refreshed ai-agent-index: {n} repos → {dest}")
        # continue to list unless --refresh-only
        if getattr(args, "refresh_only", False):
            return 0

    text = format_catalog(
        include_index=bool(getattr(args, "index", False)),
        include_local=bool(getattr(args, "local", False)),
        category=getattr(args, "category", None),
        status=getattr(args, "status", None),
        q=getattr(args, "query", None),
        markdown=bool(getattr(args, "markdown", False)),
        max_index=getattr(args, "limit", None),
    )
    if getattr(args, "out", None):
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text)
    return 0 if not check_catalog() else 1


def _cmd_cycle(args: argparse.Namespace) -> int:
    if args.doc:
        print(render_cycle_doc())
        return 0
    from looplab.cycle import get_profile, list_profiles, load_cycle_state, save_cycle_state

    if args.list_profiles:
        for name in list_profiles():
            meta = get_profile(name)
            print(f"  {name:16} {meta.get('title')} — {meta.get('source')}")
        return 0

    project = Path(args.project) if args.project else None
    profile = (args.profile or "opav").strip().lower()
    try:
        get_profile(profile)
    except KeyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if project:
        state = load_cycle_state(project)
    else:
        state = CycleState(profile=profile)
    if args.profile:
        # switch profile resets phase to first unless also advancing on existing
        if state.profile != profile or args.reset:
            state = CycleState(profile=profile)
        else:
            state.profile = profile
    if args.reset:
        state = CycleState(profile=profile)
    if args.advance:
        n = max(1, int(args.advance))
        for _ in range(n):
            state.advance()
    if args.mutate:
        state.record_mutation()
    if args.verify is not None:
        state.record_verification(args.verify)
    if project:
        path = save_cycle_state(project, state)
        print(state.panel())
        print(f"\nsaved: {path}")
    else:
        print(state.panel())
    return 0


def _cmd_smoke(args: argparse.Namespace) -> int:
    from looplab.sources import check_catalog

    root = Path(__file__).resolve().parent.parent
    problems = check_catalog(root)
    if problems:
        print("FAIL sources:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("sources catalog: PASS")
    from looplab.cycle import CYCLE_PROFILES, CycleState

    for name in CYCLE_PROFILES:
        st = CycleState(profile=name)
        st.advance()
        print(f"  [OK] cycle profile {name} → {st.phase}")

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
    print(f"smoke: {len(examples)} example(s), failed={failed}")
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="looplab",
        description=(
            "LoopLab — external Hermes module: "
            "contract + skills (attach via junction, no hermes-agent code changes)"
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
        "attach",
        help="Attach LoopLab skills into Hermes via junctions (no core code change)",
    )
    s.add_argument("--hermes-home", default=None, help="Override HERMES_HOME")
    s.add_argument(
        "--no-cli",
        action="store_true",
        help="Skip editable install of looplab into Hermes agent venv",
    )
    s.set_defaults(func=_cmd_attach)

    s = sub.add_parser("detach", help="Detach LoopLab junctions from Hermes home")
    s.add_argument("--hermes-home", default=None, help="Override HERMES_HOME")
    s.set_defaults(func=_cmd_detach)

    s = sub.add_parser("install-hermes", help="Alias of attach")
    s.add_argument("--hermes-home", default=None)
    s.add_argument("--force", action="store_true")
    s.add_argument("--yes", action="store_true", help="ignored (attach always allowed)")
    s.set_defaults(func=_cmd_install_hermes)

    s = sub.add_parser("uninstall-hermes", help="Alias of detach")
    s.add_argument("--hermes-home", default=None)
    s.set_defaults(func=_cmd_uninstall_hermes)

    s = sub.add_parser("cron-recipe", help="Print hermes cron recipe (daily-triage / briefing)")
    s.add_argument("name", nargs="?", default="daily-triage", help="Recipe name")
    s.add_argument("--list", action="store_true", help="List recipe names")
    s.add_argument("--workdir", default="$PWD")
    s.add_argument("--deliver", default=None, help="Override deliver (default local)")
    s.set_defaults(func=_cmd_cron_recipe)

    s = sub.add_parser("cycle", help="Show cycle panel (OPAV / hermes-coding / kit)")
    s.add_argument("--doc", action="store_true", help="Full cycle documentation")
    s.add_argument("--list-profiles", action="store_true", help="List cycle profiles")
    s.add_argument(
        "--profile",
        default=None,
        help="Cycle profile: opav | hermes-coding | kit",
    )
    s.add_argument(
        "--project",
        default=None,
        help="Project dir — load/save durable state/opav-cycle.yaml",
    )
    s.add_argument(
        "--advance",
        nargs="?",
        const=1,
        type=int,
        default=None,
        help="Advance N phases (default 1 when flag present)",
    )
    s.add_argument("--reset", action="store_true", help="Reset cycle to first phase")
    s.add_argument("--mutate", action="store_true", help="Simulate a mutation")
    s.add_argument(
        "--verify",
        type=lambda x: x.lower() != "false",
        nargs="?",
        const=True,
        default=None,
    )
    s.set_defaults(func=_cmd_cycle)

    s = sub.add_parser(
        "sources",
        help="List loop + AI/agent support repos (catalog + optional full index)",
    )
    s.add_argument(
        "--index",
        action="store_true",
        help="Include full AI_PowerUp mirror (sources/ai-agent-index.yaml, 700+ repos)",
    )
    s.add_argument(
        "--local",
        action="store_true",
        help="Also discover sibling labs under C:/Dev",
    )
    s.add_argument(
        "--category",
        default=None,
        help="Filter: loop|harness|lab|agent|framework|ecosystem|memory|mcp|…",
    )
    s.add_argument("--status", default=None, help="Filter: integrated|referenced|indexed|local")
    s.add_argument("-q", "--query", default=None, help="Substring filter on id/url/role")
    s.add_argument("--markdown", action="store_true", help="Emit markdown table")
    s.add_argument("--out", default=None, help="Write listing to file")
    s.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap number of index rows when using --index",
    )
    s.add_argument(
        "--refresh-powerup",
        default=None,
        metavar="PATH",
        help="Regenerate ai-agent-index.yaml from AI_PowerUp tree (e.g. C:/Dev/AI_PowerUp)",
    )
    s.add_argument(
        "--refresh-only",
        action="store_true",
        help="With --refresh-powerup: only regenerate index, skip listing",
    )
    s.set_defaults(func=_cmd_sources)

    s = sub.add_parser("smoke", help="Validate bundled examples")
    s.set_defaults(func=_cmd_smoke)

    return p


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
