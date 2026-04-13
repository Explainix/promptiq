# Report Template

Render the report in this section order:

```text
╭──────────────────────── PromptIQ Review ────────────────────────╮
│ Score      [X.X] / 10          Band       [Foundational / Competent / Strong / Elite]
│ Signal     [Low / Medium / High] confidence   [Low / Medium / High] complexity
│ Trend      [If available: +0.3 vs last compatible session]
╰──────────────────────────────────────────────────────────────────╯

Why It Is Not Higher
[Blunt paragraph grounded in helper output]

Dimension Breakdown
Instruction Clarity    [bar]  [N]/10
Context Provision      [bar]  [N]/10
Iteration Quality      [bar]  [N]/10
Task Decomposition     [bar]  [N]/10
Output Specification   [bar]  [N]/10
Example Usage          [bar or N/A]
Reasoning Elicitation  [bar or N/A]
Tool Awareness         [bar or N/A]

Strongest Evidence
> "[Quote one real user message]"
[Explain in 1-2 crisp sentences why it was strong.]

Hardest Corrections
1. Original: "[specific weak or improvable user message]"
   Rewrite:  "[better version]"
   Why:      [short explanation]
2. Original: "[specific weak or improvable user message]"
   Rewrite:  "[better version]"
   Why:      [short explanation]

Next Session Drill
[One concrete behavior to practice next time]
```

If `history_session_count >= 3`, append:

```text
Recent Trend
[Last up to 5 compatible sessions in a compact list]

Focus Area
[Longest-running weakest dimension, with one direct sentence on what to improve]
```

Progress bars:

- Use 10 characters
- Filled = `█`
- Empty = `░`
- For N/A, render `──────────  N/A`

Style rules:

- Keep the tone sharp, calm, and slightly editorial.
- Make the layout feel composed, not like raw terminal dumps.
- Prefer short paragraphs and aligned labels over dense blocks.
- Do not use emojis.
- Avoid sounding cute or performative. Elegant beats flashy.
