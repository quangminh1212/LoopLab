"""Hermes cron recipes — cobusgreyling/loop-engineering daily-triage style."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CronRecipe:
    name: str
    schedule: str
    skill: str
    prompt: str
    deliver: str = "local"

    def as_bash(self, workdir: str = "$PWD") -> str:
        return (
            f'hermes cron create "{self.schedule}" \\\n'
            f'  --name "{self.name}" \\\n'
            f'  --deliver {self.deliver} \\\n'
            f'  --skill {self.skill} \\\n'
            f'  --workdir "{workdir}" \\\n'
            f'  "{self.prompt}"'
        )

    def as_powershell(self, workdir: str = "$PWD") -> str:
        # hermes CLI same flags on Windows
        return self.as_bash(workdir)


RECIPES: dict[str, CronRecipe] = {
    "daily-triage": CronRecipe(
        name="Daily triage",
        schedule="0 7 * * 1-5",
        skill="loop-triage",
        prompt=(
            "Run loop-triage. Read STATE.md. Merge findings into High Priority and Watch List. "
            "Update Last run timestamp. Do not edit source code. End with a 5-line summary."
        ),
    ),
    "triage-pulse": CronRecipe(
        name="Triage pulse",
        schedule="0 */2 * * *",
        skill="loop-triage",
        prompt=(
            "Run loop-triage. Report obvious small wins only. Update STATE.md. No code changes."
        ),
    ),
    "daily-briefing": CronRecipe(
        name="Daily briefing",
        schedule="0 7 * * 1-5",
        skill="looplab",
        prompt=(
            "Run LoopLab daily-briefing. Read STATE.md and loop-spec.yaml. "
            "Write reports/daily-briefing.md + receipt. No code edits. 5-line summary."
        ),
    ),
}


def list_recipes() -> list[str]:
    return sorted(RECIPES.keys())


def render_recipe(key: str, workdir: str = "$PWD", deliver: str | None = None) -> str:
    if key not in RECIPES:
        known = ", ".join(list_recipes())
        raise KeyError(f"unknown recipe {key!r}; known: {known}")
    r = RECIPES[key]
    if deliver:
        r = CronRecipe(r.name, r.schedule, r.skill, r.prompt, deliver)
    lines = [
        f"# LoopLab cron recipe: {key}",
        "# Week 1: keep --deliver local until you trust output.",
        "",
        r.as_bash(workdir),
        "",
        "# Ops",
        "# hermes cron list",
        "# hermes cron status",
        "# hermes cron pause <job-id>",
        "# hermes cron remove <job-id>",
        "",
        "# Pattern docs: patterns/hermes/daily-triage.md",
    ]
    return "\n".join(lines)
