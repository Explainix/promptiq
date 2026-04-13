---
name: install
description: Install PromptIQ on the current machine. Detects the environment (Claude Code or Codex CLI) and runs the appropriate installation steps automatically. Trigger with /install.
triggers:
  - /install
---

You are installing PromptIQ, a skill that scores AI prompting proficiency. Follow these steps exactly.

## Step 1: Detect environment

Run both checks in parallel:

```bash
claude --version 2>/dev/null && echo "CLAUDE_CODE=yes" || echo "CLAUDE_CODE=no"
```

```bash
codex --version 2>/dev/null && echo "CODEX=yes" || echo "CODEX=no"
```

## Step 2: Install based on environment

### If Claude Code is detected

```bash
claude plugin marketplace add Explainix/promptiq 2>&1
```

Then:

```bash
claude plugin install promptiq 2>&1
```

### If Codex CLI is detected

```bash
mkdir -p ~/.codex/skills/promptiq && \
curl -fsSL -o ~/.codex/skills/promptiq/SKILL.md \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/score/SKILL.md && \
echo "OK"
```

### If neither is detected

Report: "PromptIQ supports Claude Code and Codex CLI. Neither was found on this machine. Please install one first: https://claude.ai/claude-code"

## Step 3: Verify Python 3 is available

```bash
python3 --version 2>/dev/null || echo "PYTHON_MISSING"
```

If `PYTHON_MISSING`: warn the user — "Note: Python 3 is required for history persistence. Without it, /score will still work but scores won't be saved between sessions."

## Step 4: Confirm installation

Report the result clearly:

```
PromptIQ installed successfully.

  Tool:     [Claude Code / Codex CLI]
  Trigger:  /score
  History:  ~/.claude/promptiq/history.json
  Python 3: [found / not found — history persistence disabled]

Run /score at the end of any session to get your first score.
```
