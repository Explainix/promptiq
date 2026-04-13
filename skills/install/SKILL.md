---
name: install
description: Install PromptIQ on the current machine. Detects the AI CLI environment and installs to the appropriate skills directory. Works with Claude Code, Codex CLI, and any AI CLI that supports skill files. Trigger with /install.
triggers:
  - /install
---

You are installing PromptIQ, a skill that scores AI prompting proficiency. Follow these steps exactly.

## Step 1: Detect environment

Run these checks to identify which AI CLI tools are available:

```bash
claude --version 2>/dev/null && echo "CLAUDE_CODE=yes" || echo "CLAUDE_CODE=no"
codex --version 2>/dev/null && echo "CODEX=yes" || echo "CODEX=no"
```

Also check which skills directory exists or is writable:

```bash
ls ~/.claude/skills/ 2>/dev/null && echo "CLAUDE_SKILLS=yes" || echo "CLAUDE_SKILLS=no"
ls ~/.codex/skills/ 2>/dev/null && echo "CODEX_SKILLS=yes" || echo "CODEX_SKILLS=no"
```

## Step 2: Install based on environment

Use the first matching case:

### Claude Code (plugin system)

If `CLAUDE_CODE=yes`:

```bash
claude plugin marketplace add Explainix/promptiq 2>&1 && \
claude plugin install promptiq 2>&1
```

### Codex CLI

If `CODEX=yes`:

```bash
mkdir -p ~/.codex/skills/promptiq && \
curl -fsSL -o ~/.codex/skills/promptiq/SKILL.md \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/score/SKILL.md && \
echo "OK"
```

### Any other AI CLI with a skills directory

If a `~/.*/skills/` directory exists for another tool, install there:

```bash
SKILLS_DIR="<detected skills directory>/promptiq"
mkdir -p "$SKILLS_DIR" && \
curl -fsSL -o "$SKILLS_DIR/SKILL.md" \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/score/SKILL.md && \
echo "OK"
```

### Fallback: manual instructions

If no known environment is detected, report:

```
PromptIQ could not detect a supported AI CLI.

To install manually, copy SKILL.md to your AI tool's skills directory:

  curl -fsSL https://raw.githubusercontent.com/Explainix/promptiq/main/skills/score/SKILL.md \
    > /path/to/your/skills/promptiq/SKILL.md

Then trigger with /score in any session.

Supported tools: Claude Code, Codex CLI, or any AI CLI that loads Markdown skill files.
```

## Step 3: Verify Python 3 is available

```bash
python3 --version 2>/dev/null || echo "PYTHON_MISSING"
```

If `PYTHON_MISSING`: warn — "Note: Python 3 is required for history persistence. Without it, /score will still work but scores won't be saved between sessions."

## Step 4: Confirm installation

```
PromptIQ installed successfully.

  Tool:     [detected tool name]
  Trigger:  /score
  History:  ~/.promptiq/history.json
  Python 3: [found vX.X / not found — history persistence disabled]

Run /score at the end of any session to get your first score.
```
