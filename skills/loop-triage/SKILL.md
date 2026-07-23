---
name: loop-triage
description: >
  Daily / event triage loop for Hermes. Read STATE.md, scan recent signals
  (git status, CI hints, open issues if available), update High Priority and
  Watch List, write a short summary. Report-only by default; no source edits
  unless the prompt explicitly allows a bounded fix.
---

# loop-triage

## Defaults
- Risk: **L1** (read-only report)
- Deliver: prefer `local` when scheduled via cron
- State file: `STATE.md` at workdir root
- Pause flag: if `loop-pause-all: true` in STATE.md → exit immediately with "paused"

## Steps
1. Read `STATE.md`. If missing, create a minimal skeleton and continue.
2. Observe repo/signals (cheap first):
   - `git status -sb` / recent log if git repo
   - obvious TODO/FIXME only if already in open files or STATE
   - do not deep-crawl the entire monorepo
3. Classify into:
   - **High Priority** — broken build, security, data loss risk
   - **Watch List** — smell, debt, follow-ups
4. Update STATE.md timestamps and lists (merge, don't wipe history blindly).
5. Optional: if prompt allows "propose patch only", emit a fenced unified diff — **do not apply**.
6. End with a **5-line summary** suitable for cron delivery.

## Verification
- STATE.md has `Last run` updated
- Summary ≤ 5 lines
- No source tree edits unless explicitly requested and risk ≤ L2

## Cron example
```bash
hermes cron create "0 7 * * 1-5" \
  --name "Daily triage" \
  --deliver local \
  --skill loop-triage \
  --workdir "$PWD" \
  "Run loop-triage. Read STATE.md. Merge findings. No code edits. 5-line summary."
```
