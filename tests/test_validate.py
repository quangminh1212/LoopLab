from pathlib import Path

from looplab.io_util import load_spec
from looplab.score import score_spec
from looplab.validate import validate_spec

ROOT = Path(__file__).resolve().parents[1]


def test_daily_briefing_valid():
    spec = load_spec(ROOT / "examples/daily-briefing/loop-spec.yaml")
    r = validate_spec(spec)
    assert r.ok, r.errors
    s = score_spec(spec)
    assert s.score >= 70


def test_daily_triage_valid():
    spec = load_spec(ROOT / "examples/daily-triage/loop-spec.yaml")
    r = validate_spec(spec)
    assert r.ok, r.errors


def test_prompt_only_invalid_or_weak():
    spec = load_spec(ROOT / "examples/prompt-only/loop-spec.yaml")
    r = validate_spec(spec)
    s = score_spec(spec)
    assert (not r.ok) or s.score < 40
