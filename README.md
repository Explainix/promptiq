# PromptIQ

A skill that scores your AI prompting proficiency and tracks improvement over time. Works with any AI CLI that supports Markdown skill files — Claude Code, Codex CLI, and others.

## What it does

Run `/score` at the end of any session to get:

- A score across 8 dimensions of prompt quality (1–10 each)
- Specific improvement suggestions with quotes from your session
- Trend tracking vs. your previous sessions

## Requirements

- Python 3.6+ (for history persistence — pre-installed on macOS and most Linux distros)

## Installation

### Let the agent install it for you

Paste this into any session:

```
Read https://raw.githubusercontent.com/Explainix/promptiq/main/skills/install/SKILL.md and follow the instructions to install PromptIQ.
```

### Claude Code

```bash
claude plugin marketplace add Explainix/promptiq
claude plugin install promptiq
```

### Codex CLI

```bash
mkdir -p ~/.codex/skills/promptiq
curl -fsSL -o ~/.codex/skills/promptiq/SKILL.md \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/score/SKILL.md
```

### Any other AI CLI

Copy `skills/score/SKILL.md` to your tool's skills directory and trigger with `/score`.

## Usage

**Claude Code:** run `/score` in any session.

**Codex CLI:** run `/score` or just say "score my prompting" — Codex matches skills by description automatically. Restart Codex after installing to pick up the skill.

**Other AI CLIs:** trigger depends on your tool's skill loading mechanism.

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

All data is stored locally at `~/.promptiq/history.json`. Nothing is uploaded.

## Files

| File | Purpose |
|------|---------|
| `skills/score/SKILL.md` | Scoring skill — works in any AI CLI |
| `skills/install/SKILL.md` | Agent-driven installer |
| `.claude-plugin/` | Claude Code plugin manifest |
