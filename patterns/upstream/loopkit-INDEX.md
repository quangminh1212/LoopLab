# LoopKit skill index (reference)

Upstream: [Archive228/loopkit](https://github.com/Archive228/loopkit) — 33 battle-tested skills + minimal harness for coding agents.

LoopLab does **not** vendor the full skill pack (license/size). When you need coding-agent micro-skills (TDD, review, worktree, PR), consult LoopKit and map into a `loop-spec` + `/looplab` multi-step mode.

## Map to LoopLab

| LoopKit idea | LoopLab surface |
|--------------|-----------------|
| Minimal harness | `looplab init` + STATE.md + receipt |
| Skills for agents | `skills/looplab/agents/*` + mode build/patch/audit |
| Verification before done | `looplab validate` / `score` / dry-run receipt |
| OPAV discipline | `looplab cycle --project . --advance` |

## Install upstream (optional)

```bash
# outside LoopLab — use as agent skill pack for Claude/Cursor
git clone https://github.com/Archive228/loopkit
```
