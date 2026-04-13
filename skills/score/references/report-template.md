# Report Template

Render the report in this section order:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PromptIQ Review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Total:                [X.X] / 10 [trend if available]
  Confidence:           [Low / Medium / High]
  Complexity:           [Low / Medium / High]
  Band:                 [Foundational / Competent / Strong / Elite]

  Why It Is Not Higher
  [Blunt paragraph grounded in helper output]

  Instruction Clarity   [bar]  [N]/10
  Context Provision     [bar]  [N]/10
  Iteration Quality     [bar]  [N]/10
  Task Decomposition    [bar]  [N]/10
  Output Specification  [bar]  [N]/10
  Example Usage         [bar or N/A]
  Reasoning Elicitation [bar or N/A]
  Tool Awareness        [bar or N/A]

  Strongest Evidence
  [Quote one real user message and explain why it was strong]

  Hardest Correction
  1. [Specific criticism with exact quote]
     Better version: "[rewritten version]"
  2. [Specific criticism with exact quote]
     Better version: "[rewritten version]"

  Next Session Drill
  [One concrete behavior to practice next time]
```

If `history_session_count >= 3`, append:

```text
  Recent Trend
  [Last up to 5 compatible sessions]

  Focus Area
  [Longest-running weakest dimension]
```

Progress bars:

- Use 10 characters
- Filled = `█`
- Empty = `░`
- For N/A, render `──────────  N/A`
