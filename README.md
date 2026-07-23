# LoopLab

**Hermes-native loop engineering lab** — 4 lớp đã được **vendor vào repo** (không chỉ link):

| Lớp | Nguồn | Trong LoopLab |
|---|---|---|
| **Contract L0–L5** | [agent-loop-engineering-kit](https://github.com/AlekseiUL/agent-loop-engineering-kit) | `looplab validate/score/dry-run/privacy-scan` + receipt |
| **Multi-step skill** | [loop-engineer](https://github.com/vibhasdutta/loop-engineer) (Hermes platform) | `skills/looplab/` + `agents/` + `scripts/init-loop.*` |
| **Triage + cron + STATE** | [cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering) | `skills/loop-triage/`, `patterns/hermes/`, `looplab cron-recipe` |
| **OPAV cycle** | [proofrail / LoopCraft](https://github.com/410979729/proofrail-hermes) | `looplab/cycle.py`, `looplab cycle`, cycle[] trong loop-spec |

```text
prompt  →  loop-spec (L0–L5)  →  validate/score/dry-run
                                →  /looplab multi-agent (delegate_task)
                                →  STATE.md + hermes cron (deliver local)
                                →  observe→plan→act→verify→closeout + receipt
```

## Cài đặt

```powershell
cd C:\Dev\LoopLab
python -m pip install -e ".[dev]"
python -m looplab install-hermes --force
```

Cài skill vào `~/.hermes/skills/looplab` (agents + init scripts) và `loop-triage`.

## CLI

| Lệnh | Nguồn logic |
|---|---|
| `looplab init` | scaffold project + STATE + HERMES |
| `looplab validate` | kit schema + safety (danger aliases, L3 isolation, cron L3 block) |
| `looplab score` | kit category weights (contract/safety/verification/…) |
| `looplab dry-run` | kit contract dry-run + receipt |
| `looplab privacy-scan` | kit secret/path scan |
| `looplab cron-recipe daily-triage` | cobus hermes cron |
| `looplab cycle` / `cycle --doc` | LoopCraft OPAV panel |
| `looplab install-hermes` | vendor skills → Hermes home |
| `looplab smoke` | examples regression |

## Multi-step trong Hermes

```text
/looplab
```

Hoặc `/looplab build|research|patch|audit` — team: resource-scout, researcher, planner, agent-factory, executor, auditor, verifier, memory-keeper qua `delegate_task`.

Init loop stack:

```powershell
& "$env:USERPROFILE\.hermes\skills\looplab\scripts\init-loop.ps1" `
  -LoopId "my-goal" -Goal "..." -Stop "..." -Git no -Mode build -Platform hermes
```

## Cron triage (tuần 1 = local)

```powershell
python -m looplab cron-recipe daily-triage
# paste lệnh hermes cron create ... --deliver local --skill loop-triage
```

Pattern đầy đủ: `patterns/hermes/daily-triage.md`, `patterns/hermes/pr-babysitter.md`.

## Cấu trúc

```text
LoopLab/
  looplab/                 # CLI package (contract + cycle + cron + install)
  skills/looplab/          # multi-step skill + agents + init-loop scripts
  skills/loop-triage/      # cobus triage skill
  patterns/hermes/         # cron / triage docs
  patterns/opav/           # LoopCraft design notes
  templates/               # loop-spec, STATE, HERMES, budget/run-log
  examples/                # daily-briefing, daily-triage, prompt-only
  schemas/                 # loop-spec.schema.json
```

## Test

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m looplab smoke
python -m looplab cron-recipe daily-triage
python -m looplab cycle --doc
```

## License

MIT — code LoopLab; upstream patterns MIT-compatible, see [SOURCES.md](SOURCES.md).
