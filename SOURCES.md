# Sources — ideas integrated into LoopLab

LoopLab is an **original integration layer**, not a vendor fork. Patterns below were studied from public repos and reimplemented for a single Hermes-focused lab.

| Upstream | Role in LoopLab |
|---|---|
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | Host runtime: skills, cron, `/goal`, `delegate_task`, memory |
| [AlekseiUL/agent-loop-engineering-kit](https://github.com/AlekseiUL/agent-loop-engineering-kit) | Loop contract: risk classes L0–L5, validate/score/dry-run/receipt |
| [vibhasdutta/loop-engineer](https://github.com/vibhasdutta/loop-engineer) | Multi-agent outer loop skill shape for Hermes (`/looplab`) |
| [cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering) | Hermes daily-triage + `hermes cron` + STATE.md patterns |
| [410979729/proofrail-hermes](https://github.com/410979729/proofrail-hermes) (LoopCraft) | Observe → plan → act → verify → closeout execution discipline |
| [Siddhant-Goswami/Crucible](https://github.com/Siddhant-Goswami/Crucible) | Bounded act→verify harness idea (adapter mindset) |

## Design rule

> A loop is not done because the agent says so. It is done when verification passes, stop reason is recorded, and a receipt exists.

## What LoopLab does *not* copy

- Full multi-agent orchestration engines from loop-engineer (scripts/agents trees)
- Proofrail plugin binary / hook runtime (use upstream if needed)
- Full cobus greyling CLI (`loop-init`, `loop-audit` npm package)

LoopLab keeps a **lean contract + Hermes skills + install helpers** path.
