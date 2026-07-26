# Sources — vendored + AI/agent support links

Machine-readable:

| File | Role | CLI |
|------|------|-----|
| [`sources/catalog.yaml`](sources/catalog.yaml) | Core: loop engineering + harness catalogs + sibling labs + high-signal agents | `looplab sources` |
| [`sources/ai-agent-index.yaml`](sources/ai-agent-index.yaml) | Full mirror of AI_PowerUp (700+ OSS AI/agent repos) | `looplab sources --index` |

## Loop engineering (integrated into LoopLab)

| Upstream | License | Integration |
|---|---|---|
| [AlekseiUL/agent-loop-engineering-kit](https://github.com/AlekseiUL/agent-loop-engineering-kit) | MIT | **integrated** — validate/score/privacy/receipt + cycle profile `kit` |
| [vibhasdutta/loop-engineer](https://github.com/vibhasdutta/loop-engineer) | MIT | **integrated** — `skills/looplab/` multi-step |
| [cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering) | MIT | **integrated** — triage, cron, patterns/hermes |
| [410979729/proofrail-hermes](https://github.com/410979729/proofrail-hermes) | check | **integrated** — OPAV cycle profile `opav` |
| [douglas-ou/hermes-coding](https://github.com/douglas-ou/hermes-coding) | MIT | **integrated** — cycle profile `hermes-coding` |
| [Archive228/loopkit](https://github.com/Archive228/loopkit) | MIT | **integrated** — `patterns/upstream/loopkit-INDEX.md` map |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | MIT | **integrated** — attach host |
| [FareedKhan-dev/agentic-loop-engineering-course](https://github.com/FareedKhan-dev/agentic-loop-engineering-course) | check | referenced — education |
| [breath57/how-agent-loop-engineering](https://github.com/breath57/how-agent-loop-engineering) | check | referenced — deep-dive series |

## Agent harness catalogs (improve AI agents)

| Repo | Role |
|------|------|
| [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) | Harness engineering awesome + templates |
| [Picrew/awesome-agent-harness](https://github.com/Picrew/awesome-agent-harness) | Implementation-first harness project list |
| [RUCAIBox/awesome-agent-harness](https://github.com/RUCAIBox/awesome-agent-harness) | Survey / paper list |
| [walkinglabs/awesome-harness-engineering](https://github.com/walkinglabs/awesome-harness-engineering) | Tools & guides |
| [DenisSergeevitch/agents-best-practices](https://github.com/DenisSergeevitch/agents-best-practices) | Production harness skill pack |
| [Skytliang/Multi-Agents-Debate](https://github.com/Skytliang/Multi-Agents-Debate) | MAD engine (NexusLab) |
| [thunlp/ChatEval](https://github.com/thunlp/ChatEval) | Evaluator personas |
| [YerbaPage/SWE-Debate](https://github.com/YerbaPage/SWE-Debate) | SWE multi-agent debate |
| [obra/superpowers](https://github.com/obra/superpowers) | Cross-agent skills + TDD methodology |

## AI ecosystem hub

| Hub | Role |
|-----|------|
| [quangminh1212/AI_PowerUp](https://github.com/quangminh1212/AI_PowerUp) | **732** curated repos: agents, frameworks, RAG, MCP, eval, training, vision, audio, … Local: `C:/Dev/AI_PowerUp` |

Refresh local index from a live tree:

```powershell
python -m looplab sources --refresh-powerup C:\Dev\AI_PowerUp --refresh-only
```

## Sibling labs (AI/agent support stack)

| Lab | URL | Role |
|-----|-----|------|
| AgentLab | https://github.com/quangminh1212/AgentLab | Memory + skills + integrations hub |
| NexusLab | https://github.com/quangminh1212/NexusLab | Multi-AI harness / MAD / AHE |
| CrewLab | https://github.com/quangminh1212/CrewLab | Multi-agent crew + DeerFlow |
| JarvisLab | https://github.com/quangminh1212/JarvisLab | Voice MCP for agents |
| WorkerLab | https://github.com/quangminh1212/WorkerLab | Agent activity monitor |
| CloneLab | https://github.com/quangminh1212/CloneLab | Clone registry + lineage |
| RouterLab | https://github.com/quangminh1212/RouterLab | Multi-provider AI router |
| TokenLab | https://github.com/quangminh1212/TokenLab | Token usage & cost tracker |
| AI_BenchLab | https://github.com/quangminh1212/AI_BenchLab | LLM benchmark / identity probe |
| Hermes_Zalo | https://github.com/quangminh1212/Hermes_Zalo | Zalo bridge for Hermes |
| MythLab | https://github.com/quangminh1212/MythLab | Creative writing AI lab |

## High-signal agents & frameworks (subset)

Full list: `looplab sources --index --category agents` / `--category frameworks`.

Examples in core catalog: OpenHands, Codex, Claude Code, Aider, SWE-agent, Continue, Goose, CrewAI, AutoGen, LangGraph, LangChain, smolagents, PydanticAI, DeerFlow, browser-use, mem0, MCP servers.

## CLI

```powershell
python -m looplab sources                          # core catalog + check
python -m looplab sources --category harness
python -m looplab sources --category lab
python -m looplab sources --index                  # +700 AI_PowerUp repos
python -m looplab sources --index --category agents -q coding
python -m looplab sources --markdown --out sources/LINKS.md
python -m looplab sources --local                  # also scan C:/Dev labs
```

## Rule preserved

> A loop is not done because an agent says it is done. It is done when verification passes, the stop reason is recorded, and the receipt is readable.
