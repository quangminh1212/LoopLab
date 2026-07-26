import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "looplab", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_validate_ok():
    p = run("validate", "examples/daily-briefing/loop-spec.yaml")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "PASS" in p.stdout


def test_cli_score():
    p = run("score", "examples/daily-briefing/loop-spec.yaml")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "score:" in p.stdout


def test_cli_dry_run(tmp_path: Path):
    out = tmp_path / "run"
    p = run("dry-run", "examples/daily-triage/loop-spec.yaml", "--out", str(out))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (out / "receipt.md").is_file()
    assert (out / "run-record.yaml").is_file()


def test_cli_smoke():
    p = run("smoke")
    assert p.returncode == 0, p.stdout + p.stderr


def test_cli_init(tmp_path: Path):
    target = tmp_path / "proj"
    p = run("init", str(target))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (target / "loop-spec.yaml").is_file()
    assert (target / "STATE.md").is_file()


def test_cli_accepts_project_directory(tmp_path: Path):
    """User flow: init dir then validate/score/dry-run with the directory path."""
    target = tmp_path / "loop-dir"
    p = run("init", str(target))
    assert p.returncode == 0, p.stdout + p.stderr
    p = run("validate", str(target))
    assert p.returncode == 0, p.stdout + p.stderr
    assert "PASS" in p.stdout
    p = run("score", str(target))
    assert p.returncode == 0, p.stdout + p.stderr
    assert "score:" in p.stdout
    p = run("dry-run", str(target), "--out", "runs/dry-run")
    assert p.returncode == 0, p.stdout + p.stderr
    assert (target / "runs" / "dry-run" / "receipt.md").is_file()


def test_cli_cycle_advance_persists(tmp_path: Path):
    target = tmp_path / "cycle-proj"
    p = run("init", str(target))
    assert p.returncode == 0, p.stdout + p.stderr
    p = run("cycle", "--project", str(target), "--advance")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "phase: **plan**" in p.stdout
    assert (target / "state" / "opav-cycle.yaml").is_file()
    p = run("cycle", "--project", str(target), "--advance")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "phase: **act**" in p.stdout


def test_cli_sources_and_hermes_coding_profile():
    p = run("sources")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "check: PASS" in p.stdout
    assert "ai-powerup" in p.stdout.lower() or "AI_PowerUp" in p.stdout or "ai-powerup" in p.stdout
    assert "agent-loop-engineering-kit" in p.stdout
    p = run("sources", "--category", "harness")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "awesome-harness" in p.stdout.lower() or "harness" in p.stdout.lower()
    p = run("sources", "--category", "lab")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "nexuslab" in p.stdout.lower() or "lab-nexuslab" in p.stdout
    p = run("sources", "--markdown")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "| Status |" in p.stdout or "LoopLab sources" in p.stdout
    # full index file must exist and be loadable via --index --limit
    assert (ROOT / "sources" / "ai-agent-index.yaml").is_file()
    p = run("sources", "--index", "--limit", "5", "--category", "agents")
    assert p.returncode == 0, p.stdout + p.stderr
    p = run("cycle", "--list-profiles")
    assert p.returncode == 0
    assert "hermes-coding" in p.stdout
    assert "kit" in p.stdout
    p = run("cycle", "--profile", "hermes-coding", "--advance")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "phase: **breakdown**" in p.stdout
