"""Install LoopLab skills into Hermes Agent home."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    # Common Windows/Linux layouts
    for candidate in (
        Path.home() / ".hermes",
        Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".hermes",
    ):
        if candidate.exists():
            return candidate
    return Path.home() / ".hermes"


def install_skills(
    hermes_home: Path | None = None,
    *,
    force: bool = False,
) -> list[Path]:
    home = hermes_home or default_hermes_home()
    src_skills = repo_root() / "skills"
    if not src_skills.is_dir():
        raise FileNotFoundError(f"skills directory missing: {src_skills}")

    dest_root = home / "skills"
    dest_root.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []

    for skill_dir in sorted(src_skills.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        dest = dest_root / skill_dir.name
        if dest.exists():
            if not force:
                # update in place files
                for item in skill_dir.rglob("*"):
                    if item.is_file():
                        rel = item.relative_to(skill_dir)
                        target = dest / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target)
                        installed.append(target)
                continue
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        installed.append(dest)

    # Project context snippet optional copy into home
    context = repo_root() / "templates" / "HERMES.md"
    if context.is_file():
        marker = home / "looplab-HERMES.md"
        shutil.copy2(context, marker)
        installed.append(marker)

    return installed
