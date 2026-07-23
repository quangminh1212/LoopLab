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

## Cài đặt & gắn vào Hermes (plugin-style, **không sửa code Hermes**)

Giống **Hermes_Zalo**: SoT ở repo riêng, Hermes chỉ nhận **junction** (skill/plugin).

```powershell
cd C:\Dev\LoopLab
python -m pip install -e ".[dev]"

# Attach — junction skills -> %LOCALAPPDATA%\hermes\skills\
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
# hoặc:
python -m looplab attach

# Detach
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\uninstall.ps1
# hoặc:
python -m looplab detach
```

| Module | SoT | Hermes nhận | Sửa hermes-agent? |
|--------|-----|-------------|-------------------|
| **Zalo** | `C:\Dev\Hermes_Zalo` | `plugins/zalo-platform` + bridge (junction) | **Không** |
| **LoopLab** | `C:\Dev\LoopLab` | `skills/looplab`, `skills/loop-triage` (junction) | **Không** |

## CLI

| Lệnh | Việc |
|---|---|
| `looplab attach` / `detach` | Gắn/gỡ skill vào Hermes (junction) |
| `looplab init` | scaffold project + STATE + HERMES |
| `looplab validate` / `score` / `dry-run` | contract L0–L5 |
| `looplab privacy-scan` | quét secret |
| `looplab cron-recipe daily-triage` | lệnh `hermes cron` |
| `looplab cycle` | panel OPAV |
| `looplab smoke` | regression examples |

## Multi-step trong Hermes (sau attach)

```text
/looplab
/looplab build|research|patch|audit
```

Init loop stack (sau attach, path trỏ SoT qua junction):

```powershell
& "$env:LOCALAPPDATA\hermes\skills\looplab\scripts\init-loop.ps1" `
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
