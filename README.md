# LoopLab

**Hermes-native loop engineering lab** — thiết kế contract, validate/score/dry-run, cài skill Hermes, và chạy vòng **observe → plan → act → verify → closeout** với receipt.

```text
prompt mơ hồ  →  loop-spec  →  validate/score  →  dry-run receipt
                                              →  manual Hermes run
                                              →  hermes cron (deliver local)
```

## Tích hợp từ đâu?

LoopLab **gộp ý tưởng** (không fork nguyên repo) từ:

| Nguồn | Góp phần |
|---|---|
| [hermes-agent](https://github.com/NousResearch/hermes-agent) | Runtime: skills, cron, `/goal`, `delegate_task` |
| [agent-loop-engineering-kit](https://github.com/AlekseiUL/agent-loop-engineering-kit) | Risk L0–L5, validate/score/dry-run/receipt |
| [loop-engineer](https://github.com/vibhasdutta/loop-engineer) | Skill multi-step autonomous loop cho Hermes |
| [loop-engineering](https://github.com/cobusgreyling/loop-engineering) | Daily triage + `hermes cron` + STATE.md |
| [proofrail-hermes / LoopCraft](https://github.com/410979729/proofrail-hermes) | Kỷ luật OPAV + verify-after-mutation |
| [Crucible](https://github.com/Siddhant-Goswami/Crucible) | Bounded act→verify harness mindset |

Chi tiết: [SOURCES.md](SOURCES.md).

## Cài đặt

```bash
cd C:\Dev\LoopLab
python -m pip install -e ".[dev]"
looplab --help
# hoặc
python -m looplab --help
```

Cài skill vào Hermes:

```powershell
python -m looplab install-hermes
# hoặc
.\scripts\install_hermes.ps1
```

## CLI

| Lệnh | Việc |
|---|---|
| `looplab init <dir\|file.yaml>` | Scaffold project hoặc 1 loop-spec |
| `looplab validate <spec>` | Schema + safety gates |
| `looplab score <spec>` | Chấm 0–100 (ready / usable / partial / not_loop_engineered) |
| `looplab dry-run <spec> --out runs/x` | Run-record + receipt (**không** chạy Hermes) |
| `looplab render-receipt <record>` | Markdown receipt |
| `looplab install-hermes` | Copy skills → `~/.hermes/skills/` |
| `looplab smoke` | Validate examples |

## Golden path (10 phút)

```bash
looplab init ./my-loop
looplab validate ./my-loop/loop-spec.yaml
looplab score ./my-loop/loop-spec.yaml
looplab dry-run ./my-loop/loop-spec.yaml --out ./my-loop/runs/first
```

Sau dry-run: mở Hermes trong project, gõ `/looplab` hoặc:

```text
Use loop-spec.yaml as contract for one manual read-only run.
Update STATE.md. Write receipt. Do not create cron jobs yet.
```

Cron (tuần 1, deliver local):

```bash
hermes cron create "0 7 * * 1-5" \
  --name "Daily triage" \
  --deliver local \
  --skill loop-triage \
  --workdir "$PWD" \
  "Run loop-triage. Read STATE.md. No code edits. 5-line summary."
```

## Skills Hermes

- `skills/looplab/SKILL.md` — `/looplab` design|run|triage|goal  
- `skills/loop-triage/SKILL.md` — triage lặp (cron-friendly)

## Risk classes

| Class | Ý nghĩa |
|---|---|
| L0 | Advisory một lần |
| L1 | Báo cáo read-only lặp |
| L2 | Ghi report/state local |
| L3 | Sửa repo (worktree + tests + verifier) |
| L4 | Side-effect ngoài (duyệt mỗi lần) |
| L5 | Tiền/secrets/xóa/prod (chặn trừ khi approve + rollback) |

## Cấu trúc repo

```text
LoopLab/
  looplab/          # CLI package
  schemas/          # loop-spec schema
  templates/        # loop-spec, STATE, HERMES
  skills/           # Hermes skills
  examples/         # daily-briefing, daily-triage, prompt-only (weak)
  scripts/          # install helpers
  tests/
```

## Test

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m looplab smoke
```

## Không phải gì

- Không thay Hermes runtime / gateway  
- Dry-run **không** thực thi agent  
- Không bật cron L4/L5 giúp bạn “an toàn” — contract chỉ **bắt buộc mô tả** gates  

## License

MIT
