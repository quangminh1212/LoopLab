"""GitHub + local catalog of loop engineering and AI/agent support repos."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def catalog_path() -> Path:
    return repo_root() / "sources" / "catalog.yaml"


def ai_agent_index_path() -> Path:
    return repo_root() / "sources" / "ai-agent-index.yaml"


@dataclass
class SourceEntry:
    id: str
    url: str
    license: str = ""
    status: str = "referenced"
    role: str = ""
    category: str = ""
    evidence: list[str] = field(default_factory=list)
    local_path: str = ""
    name: str = ""
    path: str = ""
    source_file: str = "catalog"


def _entry_from_dict(e: dict[str, Any], source_file: str = "catalog") -> SourceEntry | None:
    if not isinstance(e, dict):
        return None
    eid = str(e.get("id") or "").strip()
    url = str(e.get("url") or "").strip()
    if not eid and not url:
        return None
    if not eid:
        eid = re.sub(r"[^a-z0-9]+", "-", url.rstrip("/").split("/")[-1].lower()).strip("-")
    return SourceEntry(
        id=eid,
        url=url,
        license=str(e.get("license") or ""),
        status=str(e.get("status") or "referenced"),
        role=str(e.get("role") or ""),
        category=str(e.get("category") or ""),
        evidence=[str(x) for x in (e.get("evidence") or [])],
        local_path=str(e.get("local_path") or ""),
        name=str(e.get("name") or ""),
        path=str(e.get("path") or ""),
        source_file=source_file,
    )


def load_catalog(path: Path | None = None) -> list[SourceEntry]:
    p = path or catalog_path()
    if not p.is_file():
        return []
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    out: list[SourceEntry] = []
    for e in data.get("entries") or []:
        ent = _entry_from_dict(e, source_file="catalog")
        if ent:
            out.append(ent)
    return out


def load_ai_agent_index(path: Path | None = None) -> list[SourceEntry]:
    """Load full AI/agent index (mirrored from AI_PowerUp)."""
    p = path or ai_agent_index_path()
    if not p.is_file():
        return []
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    out: list[SourceEntry] = []
    for e in data.get("entries") or []:
        ent = _entry_from_dict(e, source_file="ai-agent-index")
        if ent:
            if not ent.status:
                ent.status = "indexed"
            if not ent.category and e.get("category"):
                ent.category = str(e["category"])
            out.append(ent)
    return out


def discover_ai_powerup_gitmodules(aip_root: Path) -> list[SourceEntry]:
    """Parse AI_PowerUp/_submodules/*.gitmodules live (optional refresh path)."""
    sub = aip_root / "_submodules"
    if not sub.is_dir():
        # also accept repo root with category folders containing .gitmodules style
        sub = aip_root
    entries: list[SourceEntry] = []
    for gm in sorted(sub.glob("*.gitmodules")):
        cat = gm.stem
        text = gm.read_text(encoding="utf-8-sig")
        for block in re.split(r"\n(?=\[submodule)", text):
            m_url = re.search(r"url\s*=\s*(.+)", block)
            if not m_url:
                continue
            url = m_url.group(1).strip()
            if url.endswith(".git"):
                url = url[:-4]
            m_path = re.search(r"path\s*=\s*(.+)", block)
            path = m_path.group(1).strip() if m_path else ""
            name = path.split("/")[-1] if path else url.rstrip("/").split("/")[-1]
            rid = re.sub(r"[^a-z0-9]+", "-", f"{cat}-{name}".lower()).strip("-")
            entries.append(
                SourceEntry(
                    id=rid,
                    url=url,
                    status="indexed",
                    category=cat,
                    role=f"AI_PowerUp/{cat}",
                    name=name,
                    path=path,
                    source_file="ai-powerup-live",
                )
            )
    # dedupe by url
    seen: set[str] = set()
    uniq: list[SourceEntry] = []
    for e in entries:
        if e.url in seen:
            continue
        seen.add(e.url)
        uniq.append(e)
    return uniq


def discover_local_labs(dev_root: Path | None = None) -> list[SourceEntry]:
    """Discover C:/Dev/*Lab and known AI support directories."""
    root = dev_root or Path("C:/Dev")
    if not root.is_dir():
        return []
    known = {
        "AgentLab",
        "AI_BenchLab",
        "AI_Lab",
        "AI_PowerUp",
        "CloneLab",
        "CrewLab",
        "Hermes_Zalo",
        "JarvisLab",
        "LoopLab",
        "MCP_Hakinet",
        "MythLab",
        "NexusLab",
        "RouterLab",
        "TokenLab",
        "WorkerLab",
        "XLab_MTC",
        "XLab_Web",
        "XRouter",
        "XMultiverse",
        "XLight",
    }
    out: list[SourceEntry] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        name = child.name
        if name not in known and not name.endswith("Lab") and not name.startswith("AI_"):
            continue
        if name == "LoopLab":
            continue  # self
        rid = re.sub(r"[^a-z0-9]+", "-", f"lab-{name}".lower()).strip("-")
        # try remote
        url = ""
        git_config = child / ".git"
        if git_config.exists():
            try:
                # .git may be file (submodule) or dir
                cfg = child / ".git" / "config"
                if not cfg.is_file() and git_config.is_file():
                    # gitdir pointer — skip deep parse
                    cfg = None
                if cfg and cfg.is_file():
                    text = cfg.read_text(encoding="utf-8", errors="replace")
                    m = re.search(r"url\s*=\s*(\S+)", text)
                    if m:
                        url = m.group(1).strip()
                        if url.endswith(".git"):
                            url = url[:-4]
            except OSError:
                pass
        if not url:
            url = f"https://github.com/quangminh1212/{name}"
        out.append(
            SourceEntry(
                id=rid,
                url=url,
                status="local",
                category="lab",
                role=f"Local AI/agent support lab at {child}",
                local_path=str(child).replace("\\", "/"),
                name=name,
                source_file="local-discover",
            )
        )
    return out


def check_catalog(root: Path | None = None, entries: list[SourceEntry] | None = None) -> list[str]:
    root = root or repo_root()
    problems: list[str] = []
    for e in entries if entries is not None else load_catalog():
        if e.status != "integrated":
            continue
        if not e.evidence:
            problems.append(f"{e.id}: integrated but no evidence")
        for rel in e.evidence:
            if not (root / rel).exists():
                problems.append(f"{e.id}: missing {rel}")
        if e.local_path:
            lp = Path(e.local_path)
            if not lp.exists():
                problems.append(f"{e.id}: local_path missing {e.local_path}")
    return problems


def check_local_paths(entries: list[SourceEntry]) -> list[str]:
    """Report missing local_path for lab/ecosystem entries (advisory)."""
    missing: list[str] = []
    for e in entries:
        if not e.local_path:
            continue
        if not Path(e.local_path).exists():
            missing.append(f"{e.id}: local_path not found: {e.local_path}")
    return missing


def _category_aliases(cat: str) -> set[str]:
    """Normalize singular/plural category names (agent vs agents, …)."""
    c = cat.strip().lower()
    aliases = {c}
    if c.endswith("s") and len(c) > 1:
        aliases.add(c[:-1])
    else:
        aliases.add(c + "s")
    # explicit pairs used across catalog vs AI_PowerUp index
    pairs = {
        "agent": "agents",
        "framework": "frameworks",
        "skill": "skills",
        "model": "models",
        "platform": "platforms",
    }
    if c in pairs:
        aliases.add(pairs[c])
    for k, v in pairs.items():
        if c == v:
            aliases.add(k)
    return aliases


def filter_entries(
    entries: list[SourceEntry],
    *,
    category: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> list[SourceEntry]:
    out = entries
    if category:
        allowed = _category_aliases(category)
        out = [e for e in out if (e.category or "").lower() in allowed]
    if status:
        st = status.strip().lower()
        out = [e for e in out if (e.status or "").lower() == st]
    if q:
        needle = q.strip().lower()
        out = [
            e
            for e in out
            if needle in e.id.lower()
            or needle in e.url.lower()
            or needle in (e.role or "").lower()
            or needle in (e.name or "").lower()
            or needle in (e.category or "").lower()
        ]
    return out


def format_catalog(
    *,
    include_index: bool = False,
    include_local: bool = False,
    category: str | None = None,
    status: str | None = None,
    q: str | None = None,
    markdown: bool = False,
    dev_root: Path | None = None,
    max_index: int | None = None,
) -> str:
    core = load_catalog()
    extra: list[SourceEntry] = []
    if include_index:
        extra.extend(load_ai_agent_index())
    if include_local:
        # local discover only for labs not already in core by local_path
        known_paths = {Path(e.local_path).resolve() for e in core if e.local_path and Path(e.local_path).exists()}
        for e in discover_local_labs(dev_root):
            try:
                lp = Path(e.local_path).resolve() if e.local_path else None
            except OSError:
                lp = None
            if lp and lp in known_paths:
                continue
            if any(c.id == e.id for c in core):
                continue
            extra.append(e)

    all_entries = core + extra
    filtered = filter_entries(all_entries, category=category, status=status, q=q)
    if max_index is not None and include_index:
        # keep all core; cap only index-sourced
        core_ids = {e.id for e in core}
        kept: list[SourceEntry] = []
        idx_count = 0
        for e in filtered:
            if e.source_file == "ai-agent-index" or e.source_file == "ai-powerup-live":
                if idx_count >= max_index:
                    continue
                idx_count += 1
            kept.append(e)
        # if not including index source_file labels properly for core, just slice
        if not kept:
            filtered = filtered[:max_index]
        else:
            filtered = kept

    cats = Counter((e.category or "uncategorized") for e in filtered)
    problems = check_catalog(entries=core)

    if markdown:
        lines = [
            "# LoopLab sources — AI & agent repos",
            "",
            f"**Core catalog:** {len(core)} · **Listed:** {len(filtered)}",
            "",
            "## Categories",
            "",
        ]
        for k, v in sorted(cats.items()):
            lines.append(f"- `{k}`: {v}")
        lines.extend(["", "## Entries", ""])
        lines.append("| Status | Category | ID | URL | Role |")
        lines.append("|---|---|---|---|---|")
        for e in filtered:
            role = (e.role or "").replace("|", "\\|")
            lines.append(
                f"| {e.status} | {e.category or '-'} | `{e.id}` | [{e.url.split('/')[-1]}]({e.url}) | {role} |"
            )
        if include_index:
            idx_n = len(load_ai_agent_index())
            lines.extend(
                [
                    "",
                    f"_Full AI_PowerUp mirror: `sources/ai-agent-index.yaml` ({idx_n} repos). "
                    "Use `looplab sources --index` for complete list._",
                ]
            )
        lines.append("")
        lines.append("## Check")
        lines.append("")
        lines.append("PASS" if not problems else f"FAIL ({len(problems)})")
        for p in problems:
            lines.append(f"- {p}")
        local_miss = check_local_paths(core)
        if local_miss:
            lines.append("")
            lines.append("### Local paths (advisory)")
            for m in local_miss:
                lines.append(f"- {m}")
        return "\n".join(lines)

    lines = [
        "LoopLab sources (loop engineering + AI/agent support):",
        "",
        f"  core catalog : {len(core)}",
    ]
    if include_index:
        lines.append(f"  ai-agent index: {len(load_ai_agent_index())} (sources/ai-agent-index.yaml)")
    if include_local:
        lines.append(f"  local discover: on")
    lines.append(f"  listed now   : {len(filtered)}")
    if cats:
        lines.append("  categories   : " + ", ".join(f"{k}={v}" for k, v in sorted(cats.items())))
    lines.append("")
    for e in filtered:
        cat = e.category or "-"
        lines.append(f"  [{e.status:10}] [{cat:12}] {e.id:32} {e.url}")
        if e.role:
            lines.append(f"               {e.role}")
        if e.local_path:
            exists = Path(e.local_path).exists()
            lines.append(f"               local: {e.local_path} ({'ok' if exists else 'MISSING'})")
    lines.append("")
    lines.append("check: PASS" if not problems else f"check: FAIL ({len(problems)})")
    for p in problems:
        lines.append(f"  - {p}")
    local_miss = check_local_paths(core)
    if local_miss:
        lines.append(f"local paths: {len(local_miss)} missing (advisory)")
        for m in local_miss[:20]:
            lines.append(f"  - {m}")
    if not include_index:
        idx = ai_agent_index_path()
        if idx.is_file():
            n = len(load_ai_agent_index())
            lines.append("")
            lines.append(f"tip: full AI/agent index has {n} repos — run: looplab sources --index")
            lines.append("     markdown table: looplab sources --markdown")
            lines.append("     filter: looplab sources --category agent|framework|harness|lab|loop")
    return "\n".join(lines)


def write_ai_agent_index_from_powerup(aip_root: Path, dest: Path | None = None) -> tuple[Path, int]:
    """Regenerate sources/ai-agent-index.yaml from a live AI_PowerUp tree."""
    entries = discover_ai_powerup_gitmodules(aip_root)
    dest = dest or ai_agent_index_path()
    payload = {
        "schema_version": "1",
        "lab": "looplab",
        "source": str(aip_root / "_submodules").replace("\\", "/") + "/*.gitmodules",
        "hub": "https://github.com/quangminh1212/AI_PowerUp",
        "generated_note": "Full AI/agent repo index mirrored from AI_PowerUp for LoopLab discovery",
        "count": len(entries),
        "entries": [
            {
                "id": e.id,
                "url": e.url,
                "category": e.category,
                "name": e.name,
                "path": e.path,
                "status": "indexed",
                "role": e.role,
            }
            for e in entries
        ],
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return dest, len(entries)
