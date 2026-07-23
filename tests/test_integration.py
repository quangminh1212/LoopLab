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


def test_uninstall_hermes_is_safe():
    from looplab.install import HERMES_ARTIFACT_RELPATHS, uninstall_from_hermes
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        (home / "skills" / "looplab").mkdir(parents=True)
        (home / "skills" / "looplab" / "SKILL.md").write_text("x", encoding="utf-8")
        (home / "prefill_crew_loop.json").write_text("[]", encoding="utf-8")
        removed = uninstall_from_hermes(home)
        assert any(p.name == "looplab" or p.name == "prefill_crew_loop.json" for p in removed)
        assert not (home / "skills" / "looplab").exists()
        assert not (home / "prefill_crew_loop.json").exists()
    assert "prefill_crew_loop.json" in HERMES_ARTIFACT_RELPATHS
