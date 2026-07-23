from pathlib import Path

from looplab.cron_recipe import list_recipes, render_recipe
from looplab.cycle import CycleState, Phase, cycle_from_spec, render_cycle_doc
from looplab.io_util import load_spec
from looplab.privacy import scan
from looplab.score import score_spec
from looplab.validate import validate_spec

ROOT = Path(__file__).resolve().parents[1]


def test_opav_cycle():
    st = CycleState()
    assert st.phase == Phase.OBSERVE
    st.advance()
    assert st.phase == Phase.PLAN
    st.phase = Phase.ACT
    st.record_mutation()
    assert st.pending_verification
    st.record_verification(True)
    assert not st.pending_verification
    assert "observe" in render_cycle_doc().lower()
    spec = load_spec(ROOT / "examples/daily-briefing/loop-spec.yaml")
    assert cycle_from_spec(spec)[0] == "observe"


def test_cron_recipes():
    assert "daily-triage" in list_recipes()
    text = render_recipe("daily-triage")
    assert "hermes cron create" in text
    assert "loop-triage" in text
    assert "--deliver local" in text


def test_multi_step_skill_vendored():
    skill = ROOT / "skills/looplab/SKILL.md"
    assert skill.is_file()
    text = skill.read_text(encoding="utf-8")
    assert "delegate_task" in text
    assert "observe" in text.lower() or "OPAV" in text
    agents = ROOT / "skills/looplab/agents"
    for name in ("researcher.md", "executor.md", "planner.md", "memory-keeper.md"):
        assert (agents / name).is_file(), name
    assert (ROOT / "skills/looplab/scripts/init-loop.ps1").is_file()
    assert (ROOT / "skills/loop-triage/SKILL.md").is_file()
    assert (ROOT / "patterns/hermes/daily-triage.md").is_file()


def test_kit_score_categories():
    spec = load_spec(ROOT / "examples/daily-briefing/loop-spec.yaml")
    r = validate_spec(spec)
    assert r.ok, r.errors
    s = score_spec(spec)
    assert s.score >= 70
    assert "contract" in s.categories
    assert "safety" in s.categories


def test_privacy_scan_repo_clean_enough():
    findings = scan(ROOT)
    # no high-signal secret patterns expected in source
    bad = [f for f in findings if f["type"] in {"openai_key", "github_token", "private_key", "aws_access_key"}]
    assert not bad, bad


def test_attach_detach_hermes_junctions():
    import sys
    import tempfile
    from pathlib import Path

    from looplab.install import HERMES_ARTIFACT_RELPATHS, attach_to_hermes, uninstall_from_hermes

    if sys.platform != "win32":
        # symlink path still valid on unix
        pass
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        (home / "skills").mkdir(parents=True)
        linked = attach_to_hermes(home, install_cli=False)
        assert any(p.name == "looplab" for p in linked)
        skill = home / "skills" / "looplab"
        assert skill.exists()
        assert (skill / "SKILL.md").is_file()
        # SoT file is reachable through link
        assert "looplab" in (skill / "SKILL.md").read_text(encoding="utf-8").lower()
        removed = uninstall_from_hermes(home)
        assert any(p.name == "looplab" for p in removed)
        assert not skill.exists()
    assert "prefill_crew_loop.json" in HERMES_ARTIFACT_RELPATHS


def test_init_loop_hermes_resolves_skill_without_userprofile_dot_hermes():
    """Windows Hermes home is LOCALAPPDATA\\hermes; script must still copy agents."""
    import os
    import subprocess
    import sys
    import tempfile

    if sys.platform != "win32":
        return

    script = ROOT / "skills" / "looplab" / "scripts" / "init-loop.ps1"
    assert script.is_file()
    with tempfile.TemporaryDirectory() as td:
        env = os.environ.copy()
        # Force miss of classic ~/.hermes so resolution must use script SoT or LOCALAPPDATA
        env.pop("HERMES_HOME", None)
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                "-LoopId",
                "smoke-init",
                "-Goal",
                "test init path",
                "-Stop",
                "all tasks checked",
                "-Git",
                "no",
                "-Mode",
                "research",
                "-Platform",
                "hermes",
            ],
            cwd=td,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert r.returncode == 0, r.stdout + r.stderr
        agents = Path(td) / ".hermes" / "agents"
        assert (agents / "researcher.md").is_file(), r.stdout + r.stderr
        assert (agents / "executor.md").is_file()
        assert (Path(td) / "loop-stack" / "smoke-init" / "PLAN.md").is_file()
