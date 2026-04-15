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

**Focus Dimension**

[`weakest_dimension.label`] — [`weakest_dimension.score`]/10

[Evidence sentence from `evidence[weakest_dimension.key]`, or "No specific evidence recorded." if absent]

What strong looks like: [one sentence describing what a 8+ score on this dimension requires]

**Other Dimensions**

```text
[For each non-focus dimension, one line:]
Instruction Clarity    [bar]  [N]/10
Context Provision      [bar]  [N]/10
...
```

[Omit the focus dimension from this list. For N/A dimensions, render `──────────  N/A`]

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

**Next Step**

[If `weakest_dimension.score < 6`:]
Your [weakest_dimension.label] score was [N]. Want me to rewrite your weakest prompt from this session to show what a stronger version looks like?

[If `weakest_dimension.score >= 6`:]
Next session, try this: [one specific constraint to add based on weakest dimension — e.g., "Add an explicit output format requirement to every prompt that produces structured data"]

If `history_session_count >= 2`, append:

**Recent Trend**

| Date | Score | Weakest |
| --- | --- | --- |
| [YYYY-MM-DD] | [X.X] | [dimension] |
| [YYYY-MM-DD] | [X.X] | [dimension] |

[If `milestone` is present:]

**Milestone**
[milestone.session_count] sessions in. Your average has moved from [earliest compatible session total] to [current total]. Strongest growth: [dimension with highest positive delta across all sessions]. Still needs work: [focus_area.label].

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
