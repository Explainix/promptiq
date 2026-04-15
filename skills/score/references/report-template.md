# Report Template

Render the report in this section order:

## PromptIQ Review

| Metric | Value |
| --- | --- |
| Score | [X.X]/10 |
| Band | [foundational / competent / strong / elite] |
| Confidence | [low / medium / high] |
| Complexity | [low / medium / high] |
| Delta | [if available: +0.3 vs last compatible session] |

**Why It Is Not Higher**  
[Blunt paragraph grounded in helper output]

**Dimension Breakdown**

```text
Instruction Clarity    [bar]  [N]/10
Context Provision      [bar]  [N]/10
Iteration Quality      [bar]  [N]/10
Task Decomposition     [bar]  [N]/10
Output Specification   [bar]  [N]/10
Example Usage          [bar or N/A]
Reasoning Elicitation  [bar or N/A]
Tool Awareness         [bar or N/A]
```

**Strongest Evidence**

> "[Quote one real user message]"

[Explain in 1-2 crisp sentences why it was strong.]

**Course Corrections**

1. Input: "[specific weak or improvable user message]"  
   Patch: "[better version]"  
   Effect: [short explanation]
2. Input: "[specific weak or improvable user message]"  
   Patch: "[better version]"  
   Effect: [short explanation]

**Next Session Drill**  
[One concrete behavior to practice next time]

If `history_session_count >= 2`, append:

**Recent Trend**

| Date | Score | Weakest |
| --- | --- | --- |
| [YYYY-MM-DD] | [X.X] | [dimension] |
| [YYYY-MM-DD] | [X.X] | [dimension] |

**Focus Area**  
[Longest-running weakest dimension, with one direct sentence on what to improve]

Progress bars:

- Use 10 characters
- Filled = `█`
- Empty = `░`
- For N/A, render `──────────  N/A`

Style rules:

- Keep the tone sharp, calm, and technical.
- Make it feel clean and deliberate, not like a generic CLI dump.
- Prefer tables for summary information that might vary in width.
- Keep section headings simple and readable.
- When verification is applicable, say plainly whether the user defined how the result should be checked.
- Do not use emojis.
- Avoid sounding cute or performative. Elegant beats flashy.
