# PromptIQ

A Claude Code plugin that scores your AI proficiency and tracks improvement over time.

## What it does

Run `/score` at the end of any Claude Code session to get:

- A score across 8 dimensions of prompt quality (1–10 each)
- Specific improvement suggestions with quotes from your session
- Trend tracking vs. your previous sessions

## Installation

### Claude Code

```bash
claude plugin marketplace add https://raw.githubusercontent.com/Explainix/promptiq/main/.claude-plugin/marketplace.json
claude plugin install promptiq
```

### Codex CLI

```bash
mkdir -p ~/.codex/skills/promptiq
curl -o ~/.codex/skills/promptiq/SKILL.md \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/score/SKILL.md
```

## Usage

At any point during a session, run:

```
/score
```

PromptIQ analyzes your conversation and outputs a scored report.

- Claude Code: history saved to `~/.claude/promptiq/history.json`
- Codex: history saved to `~/.claude/promptiq/history.json` (same location)

## Dimensions scored

| Dimension | What is evaluated |
|-----------|------------------|
| 指令清晰度 | Instructions are specific and unambiguous |
| 上下文提供 | Background and "why" are provided |
| 迭代质量 | Follow-ups advance the task rather than repeat it |
| 任务分解 | Complex tasks are broken into steps |
| 输出规格 | Format, length, style are explicitly specified |
| 示例使用 | Few-shot examples used when consistency matters |
| 推理引导 | Step-by-step thinking elicited for hard problems |
| 工具意识 | Claude Code features used appropriately |

## Privacy

All data is stored locally at `~/.claude/promptiq/history.json`. Nothing is uploaded.
