"""Attach/detach LoopLab to Hermes Agent without modifying hermes-agent source.

Same external-module pattern as Hermes_Zalo:
  - SoT stays in LoopLab repo
  - Hermes home only gets junctions (skills) or is cleaned on detach
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERMES_ARTIFACT_RELPATHS: tuple[str, ...] = (
    "skills/looplab",
    "skills/loop-triage",  # legacy junction; removed on detach
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


def skill_packages(root: Path | None = None) -> list[Path]:
    skills = (root or repo_root()) / "skills"
    if not skills.is_dir():
        return []
    out: list[Path] = []
    for d in sorted(skills.iterdir()):
        if d.is_dir() and (d / "SKILL.md").is_file():
            out.append(d)
    return out


def _is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    if sys.platform != "win32":
        return False
    # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    try:
        import ctypes

        GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW  # type: ignore[attr-defined]
        GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
        GetFileAttributesW.restype = ctypes.c_uint32
        INVALID = 0xFFFFFFFF
        attrs = GetFileAttributesW(str(path))
        if attrs == INVALID:
            return False
        return bool(attrs & 0x400)
    except Exception:
        return False


def _rm_link(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if sys.platform == "win32" and (path.is_dir() or _is_link_or_junction(path)):
        # junction or dir symlink: rmdir removes link, not target
        subprocess.run(["cmd", "/c", "rmdir", str(path)], check=False, capture_output=True)
        if path.exists() and path.is_symlink():
            path.unlink(missing_ok=True)
        return
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def ensure_link(dst: Path, src: Path) -> Path:
    """Junction on Windows, symlink elsewhere. Re-points if already a link."""
    src_r = src.resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink() or _is_link_or_junction(dst):
        if _is_link_or_junction(dst) or dst.is_symlink():
            _rm_link(dst)
        else:
            raise FileExistsError(
                f"Path exists and is not a junction: {dst} — remove manually or detach first"
            )
    if sys.platform == "win32":
        r = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(dst), str(src_r)],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0 or not (dst.exists() or _is_link_or_junction(dst)):
            raise RuntimeError(f"mklink failed: {r.stdout}\n{r.stderr}")
    else:
        os.symlink(src_r, dst, target_is_directory=True)
    return dst


def hermes_agent_python(hermes_home: Path | None = None) -> Path | None:
    """Return Hermes agent venv python if present (Windows/Linux layout)."""
    home = hermes_home or default_hermes_home()
    candidates = [
        home / "hermes-agent" / "venv" / "Scripts" / "python.exe",
        home / "hermes-agent" / "venv" / "bin" / "python",
        home / "hermes-agent" / ".venv" / "Scripts" / "python.exe",
        home / "hermes-agent" / ".venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def ensure_cli_in_hermes_venv(hermes_home: Path | None = None) -> Path | None:
    """Editable-install looplab into Hermes agent venv so terminal tool can run `python -m looplab`."""
    py = hermes_agent_python(hermes_home)
    if py is None:
        return None
    root = repo_root()
    r = subprocess.run(
        [str(py), "-m", "pip", "install", "-e", str(root), "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"pip install into Hermes venv failed ({py}):\n{r.stdout}\n{r.stderr}"
        )
    return py


def attach_to_hermes(
    hermes_home: Path | None = None,
    *,
    install_cli: bool = True,
) -> list[Path]:
    """Attach LoopLab skills into Hermes via junctions/symlinks (no core patch)."""
    home = hermes_home or default_hermes_home()
    if not home.exists():
        raise FileNotFoundError(f"Hermes home not found: {home}")
    packages = skill_packages()
    if not packages:
        raise FileNotFoundError(f"no skill packages under {repo_root() / 'skills'}")

    linked: list[Path] = []
    skills_root = home / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    for pkg in packages:
        dst = skills_root / pkg.name
        ensure_link(dst, pkg)
        linked.append(dst)

    ctx = repo_root() / "templates" / "HERMES.md"
    if ctx.is_file():
        marker = home / "looplab-HERMES.md"
        shutil.copy2(ctx, marker)
        linked.append(marker)

    if install_cli:
        try:
            py = ensure_cli_in_hermes_venv(home)
            if py is not None:
                linked.append(py)
        except RuntimeError as e:
            # Skills still attached; CLI install is best-effort for terminal tool UX.
            print(f"warning: {e}", file=sys.stderr)

    return linked


def install_skills(
    hermes_home: Path | None = None,
    *,
    force: bool = False,
) -> list[Path]:
    del force
    return attach_to_hermes(hermes_home)


def uninstall_from_hermes(hermes_home: Path | None = None) -> list[Path]:
    """Detach LoopLab links/artifacts from Hermes home (SoT repo untouched)."""
    home = hermes_home or default_hermes_home()
    removed: list[Path] = []

    names = {p.name for p in skill_packages()}
    names.update({"looplab", "loop-triage", "loop-engineer"})
    for name in sorted(names):
        path = home / "skills" / name
        if path.exists() or path.is_symlink() or _is_link_or_junction(path):
            _rm_link(path)
            removed.append(path)

    for rel in HERMES_ARTIFACT_RELPATHS:
        if rel.startswith("skills/"):
            continue
        path = home / rel
        if not (path.exists() or path.is_symlink() or _is_link_or_junction(path)):
            continue
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif _is_link_or_junction(path):
            _rm_link(path)
        elif path.is_dir() and path.name in {"looplab", "looplab-patterns"}:
            shutil.rmtree(path, ignore_errors=True)
        removed.append(path)

    return removed
