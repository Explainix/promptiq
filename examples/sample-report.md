# Sample PromptIQ Report

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PromptIQ Review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Total:                7.4 / 10
  Confidence:           High
  Complexity:           High
  Band:                 Competent

  Why It Is Not Higher
  This session had real steering and decent structure, but it still fell short of the next band because the evidence density was only barely strong enough. The user constrained scope and corrected direction, but did not repeatedly control output quality across the full session.

  Instruction Clarity   ███████░░░  7/10
  Context Provision     ███████░░░  7/10
  Iteration Quality     ████████░░  8/10
  Task Decomposition    ████████░░  8/10
  Output Specification  ███████░░░  7/10
  Example Usage         ──────────  N/A
  Reasoning Elicitation ████████░░  8/10
  Tool Awareness        ███████░░░  7/10

  Strongest Evidence
  "Please review the failing deploy flow. First isolate whether the regression is in build, runtime, or auth middleware. Then propose the minimum fix and list the files you would touch."
  This is strong because it sets scope, desired reasoning order, and expected output in one move.

  Hardest Correction
  1. "That diagnosis is too broad. Narrow it to the middleware path only and compare against yesterday's behavior."
     Better version: "Limit the analysis to middleware only. Compare today's behavior against yesterday's middleware diff and exclude build/runtime."
  2. "Do not refactor unrelated modules. I only want the smallest change that restores production behavior."
     Better version: "Give me the smallest safe patch. No refactors, no naming cleanup, and no unrelated file edits."

  Next Session Drill
  Add one explicit acceptance rule to every corrective follow-up. Do not only narrow scope; say what a good answer must contain.
```
