# PromptIQ — Design Spec

**Date:** 2026-04-13
**Status:** Approved

## Overview

PromptIQ is a Claude Code skill plugin that evaluates users' AI proficiency based on their conversation patterns. It scores 8 dimensions of prompt quality, stores history locally, and provides actionable improvement suggestions with concrete examples from the session.

Future extension: Codex CLI support (same skill, different adapter).

---

## Architecture

```
promptiq/
├── skills/
│   └── score/
│       ├── SKILL.md            # skill definition, trigger: /score
│       └── prompt-template.md  # evaluation prompt template
├── package.json                # plugin metadata
└── README.md
```

**Data flow:**
1. User runs `/score`
2. Skill reads current session conversation history
3. Constructs evaluation prompt, calls Claude to score 8 dimensions (1–10 each)
4. Outputs structured report (scores + analysis + improvement suggestions)
5. Appends score to `~/.claude/promptiq/history.json`
6. If history exists, shows trend comparison

---

## Evaluation Dimensions

Each dimension scored 1–10:

| Dimension | Key | What is evaluated |
|-----------|-----|-------------------|
| 指令清晰度 | `clarity` | Instructions are specific and unambiguous |
| 上下文提供 | `context` | Background and "why" are provided |
| 迭代质量 | `iteration` | Follow-ups advance the task rather than repeat it |
| 任务分解 | `decomposition` | Complex tasks are broken into steps |
| 输出规格 | `output_spec` | Format, length, style are explicitly specified |
| 示例使用 | `examples` | Few-shot examples used when consistency matters |
| 推理引导 | `reasoning` | Step-by-step thinking elicited for hard problems |
| 工具意识 | `tool_awareness` | Claude Code features used appropriately |

---

## Output Format

```
总分：7.2 / 10  （上次：6.5，+0.7）

各维度：
  指令清晰度    ████████░░  8/10
  上下文提供    ███████░░░  7/10
  迭代质量      ██████░░░░  6/10
  任务分解      ████████░░  8/10
  输出规格      ███████░░░  7/10
  示例使用      █████░░░░░  5/10
  推理引导      ███████░░░  7/10
  工具意识      ████████░░  8/10

亮点：[specific observation from this session]

改进建议：
  1. [specific suggestion with quote from this session]
  2. [specific suggestion with quote from this session]
```

**Key constraint:** Improvement suggestions must reference specific examples from the current session — no generic advice.

---

## Persistence Schema

File: `~/.claude/promptiq/history.json`

```json
{
  "sessions": [
    {
      "date": "2026-04-13T10:23:00Z",
      "total": 7.2,
      "dimensions": {
        "clarity": 8,
        "context": 7,
        "iteration": 6,
        "decomposition": 8,
        "output_spec": 7,
        "examples": 5,
        "reasoning": 7,
        "tool_awareness": 8
      },
      "session_summary": "brief description of what was discussed"
    }
  ]
}
```

## Trend Display Logic

| History count | Display |
|---------------|---------|
| 1 session | Last vs. current comparison |
| 3+ sessions | Last 5 trend + weakest dimension highlighted |
| 10+ sessions | Above + "AI usage style profile" based on long-term patterns |

**Privacy:** History is stored locally only. No data is uploaded.

---

## Trigger

- Command: `/score`
- Behavior: mixed mode — passive data collection during session, user-initiated report generation
- Scope: analyzes the full current session conversation

---

## Future Extensions

- Codex CLI adapter (same skill logic, different conversation history source)
- `/score --history` flag to view trend without running a new evaluation
- `/score --dimension clarity` to deep-dive a single dimension
