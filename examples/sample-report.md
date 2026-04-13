# Sample PromptIQ Report

```text
╭──────────────────────── PromptIQ Review ────────────────────────╮
│ Score      7.4 / 10          Band       Competent               │
│ Signal     High confidence   High complexity                    │
│ Trend      +0.3 vs last compatible session                      │
╰──────────────────────────────────────────────────────────────────╯

Why It Is Not Higher
This session had real steering and decent structure, but it stopped short of the next band because output control was not sustained. The user narrowed scope well and corrected drift, but did not repeatedly define what a good final answer had to contain.

Dimension Breakdown
Instruction Clarity    ███████░░░  7/10
Context Provision      ███████░░░  7/10
Iteration Quality      ████████░░  8/10
Task Decomposition     ████████░░  8/10
Output Specification   ███████░░░  7/10
Example Usage          ──────────  N/A
Reasoning Elicitation  ████████░░  8/10
Tool Awareness         ███████░░░  7/10

Strongest Evidence
> "Please review the failing deploy flow. First isolate whether the regression is in build, runtime, or auth middleware. Then propose the minimum fix and list the files you would touch."

This works because it combines scope, analysis order, and deliverable shape in one move. The model is not left guessing what kind of help is needed.

Hardest Corrections
1. Original: "That diagnosis is too broad. Narrow it to the middleware path only and compare against yesterday's behavior."
   Rewrite:  "Limit the analysis to middleware only. Compare today's behavior against yesterday's middleware diff and exclude build/runtime."
   Why:      Better boundary control. It removes adjacent areas the model would otherwise keep drifting into.

2. Original: "Do not refactor unrelated modules. I only want the smallest change that restores production behavior."
   Rewrite:  "Give me the smallest safe patch. No refactors, no naming cleanup, and no unrelated file edits."
   Why:      Better output control. It defines the shape of the answer, not just the general preference.

Next Session Drill
Add one explicit acceptance rule to every corrective follow-up. Do not only narrow scope; say what a successful answer must include before the model writes it.

Recent Trend
2026-04-10   6.8   weakest: Output Specification
2026-04-12   7.1   weakest: Context Provision
2026-04-13   7.4   weakest: Output Specification

Focus Area
Output Specification is still the drag point across recent sessions. Tighten the finish line earlier and restate it whenever you correct course.
```
