# Report Template

Render the report in this section order:

```text
┌─ PROMPTIQ / SESSION DASHBOARD ───────────────────────────────────┐
│ SCORE        [X.X]/10      BAND        [FOUNDATIONAL / COMPETENT / STRONG / ELITE]
│ CONFIDENCE   [LOW / MEDIUM / HIGH]      COMPLEXITY  [LOW / MEDIUM / HIGH]
│ DELTA        [If available: +0.3 vs last compatible session]
└──────────────────────────────────────────────────────────────────┘

[WHY NOT HIGHER]
[Blunt paragraph grounded in helper output]

[DIMENSION GRID]
Instruction Clarity    [bar]  [N]/10
Context Provision      [bar]  [N]/10
Iteration Quality      [bar]  [N]/10
Task Decomposition     [bar]  [N]/10
Output Specification   [bar]  [N]/10
Example Usage          [bar or N/A]
Reasoning Elicitation  [bar or N/A]
Tool Awareness         [bar or N/A]

[BEST SIGNAL]
> "[Quote one real user message]"
[Explain in 1-2 crisp sentences why it was strong.]

[COURSE CORRECTIONS]
1. INPUT    "[specific weak or improvable user message]"
   PATCH    "[better version]"
   EFFECT   [short explanation]
2. INPUT    "[specific weak or improvable user message]"
   PATCH    "[better version]"
   EFFECT   [short explanation]

[NEXT DRILL]
[One concrete behavior to practice next time]
```

If `history_session_count >= 3`, append:

```text
[RECENT TREND]
[Last up to 5 compatible sessions in a compact telemetry-style list]

[FOCUS AREA]
[Longest-running weakest dimension, with one direct sentence on what to improve]
```

Progress bars:

- Use 10 characters
- Filled = `█`
- Empty = `░`
- For N/A, render `──────────  N/A`

Style rules:

- Keep the tone sharp, calm, and technical.
- Make it feel like a polished instrument panel, not a generic CLI dump.
- Prefer uppercase section tags, aligned telemetry labels, and compact high-signal prose.
- Use a little swagger in naming, but keep the writing disciplined.
- Do not use emojis.
- Avoid sounding cute or performative. Elegant beats flashy.
