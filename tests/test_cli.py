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
