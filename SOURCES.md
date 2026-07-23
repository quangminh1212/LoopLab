# Sources — vendored into LoopLab

LoopLab **copies and adapts** the following public materials. Not git submodules; paths below are the integration surface.

| Upstream | License | Vendored as |
|---|---|---|
| [AlekseiUL/agent-loop-engineering-kit](https://github.com/AlekseiUL/agent-loop-engineering-kit) | MIT | `looplab/validate.py` safety rules, `score.py` categories, `privacy.py`, dry-run receipt shape |
| [vibhasdutta/loop-engineer](https://github.com/vibhasdutta/loop-engineer) `platforms/hermes` | MIT | `skills/looplab/SKILL.md`, `skills/looplab/agents/**`, `skills/looplab/scripts/init-loop.*` (rebranded looplab) |
| [cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering) | MIT | triage rules in `skills/looplab/SKILL.md` (mode triage), `patterns/hermes/*`, `templates/*budget*`, STATE templates, `looplab/cron_recipe.py` |
| [410979729/proofrail-hermes](https://github.com/410979729/proofrail-hermes) (LoopCraft) | check upstream | `looplab/cycle.py` OPAV, `patterns/opav/LoopCraft-DESIGN.md` |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | MIT | host runtime mapping only |

## Rule preserved from all four

> A loop is not done because an agent says it is done. It is done when verification passes, the stop reason is recorded, and the receipt is readable.
