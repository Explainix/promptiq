# PromptIQ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code skill plugin that scores users' AI proficiency across 8 dimensions, stores history locally, and provides actionable improvement suggestions with session-specific examples.

**Architecture:** A single `/score` skill reads the current session conversation, calls Claude with a structured evaluation prompt, renders a scored report with progress bars, and appends the result to `~/.claude/promptiq/history.json`. Trend comparison is shown when history exists.

**Tech Stack:** Claude Code skill plugin (Markdown-based SKILL.md), no runtime dependencies, local JSON persistence via Bash tool.

---

## File Map

| File | Responsibility |
|------|---------------|
| `package.json` | Plugin metadata — name, version, skills entry point |
| `skills/score/SKILL.md` | Skill definition: trigger `/score`, full evaluation + persistence logic |
| `README.md` | Installation and usage instructions |

---

### Task 1: Initialize plugin package metadata

**Files:**
- Create: `package.json`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "promptiq",
  "version": "0.1.0",
  "description": "Claude Code plugin that scores your AI proficiency and tracks improvement over time",
  "keywords": ["claude-code", "plugin", "prompt-engineering", "ai-skills"],
  "license": "MIT",
  "claude": {
    "type": "plugin",
    "skills": "skills/"
  }
}
```

- [ ] **Step 2: Verify file exists**

```bash
cat package.json
```

Expected: JSON printed with `"name": "promptiq"`.

- [ ] **Step 3: Commit**

```bash
git add package.json
git commit -m "chore: init plugin package metadata"
```

---

### Task 2: Create skill directory structure

**Files:**
- Create: `skills/score/` (directory)

- [ ] **Step 1: Create directory**

```bash
mkdir -p skills/score
```

- [ ] **Step 2: Verify**

```bash
ls skills/score
```

Expected: empty directory, no error.

- [ ] **Step 3: Commit**

```bash
git add skills/
git commit -m "chore: scaffold skills/score directory"
```

---

### Task 3: Write the evaluation prompt template

This is the core of the plugin — the prompt Claude uses to score the conversation.

**Files:**
- Create: `skills/score/SKILL.md`

- [ ] **Step 1: Create `skills/score/SKILL.md`**

```markdown
---
name: score
description: Evaluate the user's AI proficiency based on this session's conversation. Scores 8 dimensions, shows trend vs history, and gives specific improvement suggestions. Trigger with /score.
triggers:
  - /score
---

You are PromptIQ, an expert evaluator of AI collaboration skills. Your job is to analyze the current conversation and score the USER's prompting behavior — not Claude's responses.

## Step 1: Read conversation history

Analyze every message the user sent in this session. Focus on:
- How they phrased requests
- Whether they provided context and constraints
- How they handled follow-ups and corrections
- Whether they decomposed complex tasks
- Whether they specified output format/length/style
- Whether they used few-shot examples
- Whether they elicited step-by-step reasoning
- Whether they used Claude Code features (file references, slash commands, etc.)

## Step 2: Score each dimension (1–10)

Score the user on these 8 dimensions. Be honest and calibrated — a 10 means expert-level, a 5 means average, a 1 means complete beginner. Most users score 4–7.

| Dimension | Key | What to evaluate |
|-----------|-----|-----------------|
| 指令清晰度 | clarity | Instructions are specific and unambiguous. Penalize vague requests like "make it better" with no criteria. |
| 上下文提供 | context | Background and "why" are provided. Penalize bare requests with no motivation or constraints. |
| 迭代质量 | iteration | Follow-ups advance the task. Penalize repeating the same ask, or accepting wrong answers without correction. |
| 任务分解 | decomposition | Complex tasks are broken into steps. Penalize single mega-prompts that try to do everything at once. |
| 输出规格 | output_spec | Format, length, style are explicitly specified. Penalize accepting whatever format Claude defaults to. |
| 示例使用 | examples | Few-shot examples used when consistency matters. N/A (score 5) if session had no tasks requiring consistency. |
| 推理引导 | reasoning | Step-by-step thinking elicited for hard problems. N/A (score 5) if session had no complex reasoning tasks. |
| 工具意识 | tool_awareness | Claude Code features used appropriately (file refs, @mentions, slash commands). N/A (score 5) if not applicable. |

## Step 3: Read history file

Use the Bash tool to read `~/.claude/promptiq/history.json`:

```bash
cat ~/.claude/promptiq/history.json 2>/dev/null || echo "NO_HISTORY"
```

If the output is `NO_HISTORY`, this is the user's first session.

## Step 4: Render the report

Output the report in this exact format:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PromptIQ Score
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  总分：[X.X] / 10  [trend line if history exists, e.g. （上次：6.5，+0.7）]

  指令清晰度    [bar]  [N]/10
  上下文提供    [bar]  [N]/10
  迭代质量      [bar]  [N]/10
  任务分解      [bar]  [N]/10
  输出规格      [bar]  [N]/10
  示例使用      [bar]  [N]/10
  推理引导      [bar]  [N]/10
  工具意识      [bar]  [N]/10

  亮点
  [One specific thing the user did well, with a direct quote from their message]

  改进建议
  1. [Specific suggestion] — 例如你在第N条消息说了"[exact quote]"，
     更好的方式是"[rewritten version]"
  2. [Second suggestion with quote and rewrite]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Progress bar rendering rules:
- Each bar is 10 chars: filled = `█`, empty = `░`
- Score 8 → `████████░░`
- Score 5 → `█████░░░░░`
- Score 10 → `██████████`

Trend line rules:
- No history: omit trend entirely
- Has history: show last total and delta (e.g. `（上次：6.5，+0.7）` or `（上次：7.0，-0.3）`)

If 3+ sessions exist, add after the report:
```
  近期趋势（最近5次）
  [list last up to 5 sessions as: YYYY-MM-DD  X.X  weakest dimension]

  重点改进方向：[the dimension with the lowest average score]
```

If 10+ sessions exist, also add:
```
  你的 AI 使用风格
  [2-3 sentence profile based on long-term patterns, e.g. "你擅长任务分解，但持续在输出规格上失分——你很少告诉 Claude 想要什么格式。"]
```

## Step 5: Save to history

Use the Bash tool to append this session to history.

First, compute the total score as the average of all 8 dimension scores (round to 1 decimal).

Then run:

```bash
# Read existing history or start fresh
HISTORY_FILE="$HOME/.claude/promptiq/history.json"
mkdir -p "$(dirname "$HISTORY_FILE")"

# Read current content
CURRENT=$(cat "$HISTORY_FILE" 2>/dev/null || echo '{"sessions":[]}')

# Build new session entry (replace values below with actual scores)
NEW_SESSION='{
  "date": "ACTUAL_ISO_DATE",
  "total": ACTUAL_TOTAL,
  "dimensions": {
    "clarity": ACTUAL_CLARITY,
    "context": ACTUAL_CONTEXT,
    "iteration": ACTUAL_ITERATION,
    "decomposition": ACTUAL_DECOMPOSITION,
    "output_spec": ACTUAL_OUTPUT_SPEC,
    "examples": ACTUAL_EXAMPLES,
    "reasoning": ACTUAL_REASONING,
    "tool_awareness": ACTUAL_TOOL_AWARENESS
  },
  "session_summary": "ACTUAL_SUMMARY"
}'

# Append using Python (available on all platforms)
python3 -c "
import json, sys
data = json.loads('''$CURRENT''')
new = json.loads('''$NEW_SESSION''')
data['sessions'].append(new)
print(json.dumps(data, indent=2, ensure_ascii=False))
" > "$HISTORY_FILE"

echo "Saved to $HISTORY_FILE"
```

Replace all `ACTUAL_*` placeholders with the real values from your scoring before running.

The `session_summary` should be a brief (5–10 word) description of what the session was about, e.g. `"设计 PromptIQ 插件架构"`.
```

- [ ] **Step 2: Verify file was created**

```bash
head -5 skills/score/SKILL.md
```

Expected: frontmatter with `name: score`.

- [ ] **Step 3: Commit**

```bash
git add skills/score/SKILL.md
git commit -m "feat: add /score skill with evaluation prompt and persistence"
```

---

### Task 4: Write README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

```markdown
# PromptIQ

A Claude Code plugin that scores your AI proficiency and tracks improvement over time.

## What it does

Run `/score` at the end of any Claude Code session to get:

- A score across 8 dimensions of prompt quality (1–10 each)
- Specific improvement suggestions with quotes from your session
- Trend tracking vs. your previous sessions

## Installation

```bash
claude plugin install promptiq
```

Or from local path during development:

```bash
claude plugin install /path/to/promptiq
```

## Usage

At any point during a session, run:

```
/score
```

PromptIQ analyzes your conversation and outputs a scored report. History is saved to `~/.claude/promptiq/history.json`.

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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with installation and usage"
```

---

### Task 5: Smoke test the skill manually

**Files:** none (manual verification)

- [ ] **Step 1: Install plugin locally**

From inside the `promptiq` directory:

```bash
claude plugin install .
```

Expected: success message, no errors.

- [ ] **Step 2: Start a test session and run `/score`**

Open Claude Code and have a short conversation (3–5 messages). Then run `/score`.

Expected output:
- Report renders with progress bars
- Scores are in 1–10 range
- Improvement suggestions quote actual messages from the session
- `~/.claude/promptiq/history.json` is created with one entry

- [ ] **Step 3: Run `/score` a second time in a new session**

Expected: trend line appears showing last score and delta.

- [ ] **Step 4: Verify history file**

```bash
cat ~/.claude/promptiq/history.json
```

Expected: valid JSON with 2 entries in `sessions` array.

- [ ] **Step 5: Commit final state**

```bash
git add -A
git commit -m "chore: verify smoke test passes"
```

---

## Self-Review Notes

**Spec coverage check:**
- Plugin metadata → Task 1
- Directory structure → Task 2
- Evaluation prompt (8 dimensions, output format, progress bars) → Task 3
- Persistence to `~/.claude/promptiq/history.json` → Task 3 Step 5
- Trend display (1 session, 3+, 10+) → Task 3 (all three cases in SKILL.md)
- README → Task 4
- Smoke test → Task 5

**No placeholders:** All steps contain actual file content or commands.

**Type consistency:** `history.json` schema used in SKILL.md matches the spec exactly (same keys: `date`, `total`, `dimensions.*`, `session_summary`).
