# PromptIQ

A skill for Claude Code and Codex CLI that scores your AI proficiency and tracks improvement over time.

## What it does

Run `/score` at the end of any session to get:

- A score across 8 dimensions of prompt quality (1–10 each)
- Specific improvement suggestions with quotes from your session
- Trend tracking vs. your previous sessions

## Installation

### Let the agent install it for you

Paste this into any Claude Code or Codex session:

```
Read https://raw.githubusercontent.com/Explainix/promptiq/main/skills/install/SKILL.md and follow the instructions to install PromptIQ.
```

### Claude Code (manual)

```bash
claude plugin marketplace add Explainix/promptiq
claude plugin install promptiq
```

Then run `/score` in any session to verify.

### Codex CLI (manual)

```bash
mkdir -p ~/.codex/skills/promptiq
curl -o ~/.codex/skills/promptiq/SKILL.md \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/score/SKILL.md
```

Then run `/score` in any session to verify.

### Manual (any AI CLI that supports skills)

Copy `skills/score/SKILL.md` to your skills directory and trigger with `/score`.

## Requirements

- Python 3.6+ (for history persistence — pre-installed on macOS and most Linux distros)

## Usage

At any point during a session, run:

```
/score
```

PromptIQ analyzes your conversation and outputs a scored report. History is saved to `~/.claude/promptiq/history.json`.

## Dimensions scored

| Dimension | What is evaluated |
|-----------|------------------|
| Instruction Clarity | Instructions are specific and unambiguous |
| Context Provision | Background and "why" are provided |
| Iteration Quality | Follow-ups advance the task rather than repeat it |
| Task Decomposition | Complex tasks are broken into steps |
| Output Specification | Format, length, style are explicitly specified |
| Example Usage | Few-shot examples used when consistency matters |
| Reasoning Elicitation | Step-by-step thinking elicited for hard problems |
| Tool Awareness | AI tool features used appropriately |

## Privacy

All data is stored locally at `~/.claude/promptiq/history.json`. Nothing is uploaded.

## Files

| File | Purpose |
|------|---------|
| `skills/score/SKILL.md` | Main skill — works in Claude Code and Codex CLI |
| `.claude-plugin/` | Claude Code plugin manifest |
