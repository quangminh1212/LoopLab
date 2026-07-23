"""Optional install/uninstall of LoopLab artifacts into Hermes home.

Default policy: LoopLab lives only at C:\\Dev\\LoopLab (external).
Do not keep loop skills / prefill / agents inside Hermes Agent home.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

# Paths we may have written under HERMES_HOME (uninstall targets)
HERMES_ARTIFACT_RELPATHS: tuple[str, ...] = (
    "skills/looplab",
    "skills/loop-triage",
    "skills/loop-engineer",
    "agents/looplab",
    "looplab-patterns",
    "looplab-HERMES.md",
    "prefill_crew_loop.json",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    local = os.environ.get("LOCALAPPDATA")
    candidates = [
        Path.home() / ".hermes",
        Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".hermes",
    ]
    if local:
        candidates.insert(0, Path(local) / "hermes")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(local) / "hermes" if local else Path.home() / ".hermes"


def _copy_tree(src: Path, dest: Path, *, force: bool) -> list[Path]:
    installed: list[Path] = []
    if force and dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        if item.is_file():
            rel = item.relative_to(src)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            installed.append(target)
    return installed


def install_skills(
    hermes_home: Path | None = None,
    *,
    force: bool = False,
) -> list[Path]:
    """Opt-in only. Prefer keeping LoopLab outside Hermes Agent."""
    home = hermes_home or default_hermes_home()
    src_skills = repo_root() / "skills"
    if not src_skills.is_dir():
        raise FileNotFoundError(f"skills directory missing: {src_skills}")

    dest_root = home / "skills"
    dest_root.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []

    for skill_dir in sorted(src_skills.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
            continue
        dest = dest_root / skill_dir.name
        installed.extend(_copy_tree(skill_dir, dest, force=force))

    agents_src = src_skills / "looplab" / "agents"
    if agents_src.is_dir():
        agents_dest = home / "agents" / "looplab"
        installed.extend(_copy_tree(agents_src, agents_dest, force=force))

    context = repo_root() / "templates" / "HERMES.md"
    if context.is_file():
        marker = home / "looplab-HERMES.md"
        shutil.copy2(context, marker)
        installed.append(marker)

    patterns = repo_root() / "patterns" / "hermes"
    if patterns.is_dir():
        dest_pat = home / "looplab-patterns" / "hermes"
        installed.extend(_copy_tree(patterns, dest_pat, force=force))

    return installed


def uninstall_from_hermes(hermes_home: Path | None = None) -> list[Path]:
    """Remove LoopLab / legacy loop prefill artifacts from Hermes Agent home."""
    home = hermes_home or default_hermes_home()
    removed: list[Path] = []
    for rel in HERMES_ARTIFACT_RELPATHS:
        path = home / rel
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
        removed.append(path)
    return removed
