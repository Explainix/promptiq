# Sample PromptIQ Report

```text
┌─ PROMPTIQ / SESSION DASHBOARD ───────────────────────────────────┐
│ SCORE        7.4/10       BAND        COMPETENT                 │
│ CONFIDENCE   HIGH         COMPLEXITY  HIGH                      │
│ DELTA        +0.3 vs last compatible session                    │
└──────────────────────────────────────────────────────────────────┘

[WHY NOT HIGHER]
This session had real steering and decent structure, but the finish line stayed too soft. Scope control was solid, course correction happened on time, yet the user did not keep specifying what a successful final answer had to contain.

[DIMENSION GRID]
Instruction Clarity    ███████░░░  7/10
Context Provision      ███████░░░  7/10
Iteration Quality      ████████░░  8/10
Task Decomposition     ████████░░  8/10
Output Specification   ███████░░░  7/10
Example Usage          ──────────  N/A
Reasoning Elicitation  ████████░░  8/10
Tool Awareness         ███████░░░  7/10

[BEST SIGNAL]
> "Please review the failing deploy flow. First isolate whether the regression is in build, runtime, or auth middleware. Then propose the minimum fix and list the files you would touch."

This prompt is strong because it locks three things at once: scope, reasoning order, and output shape. The model is given a lane and a deliverable before it starts moving.

[COURSE CORRECTIONS]
1. INPUT    "That diagnosis is too broad. Narrow it to the middleware path only and compare against yesterday's behavior."
   PATCH    "Limit the analysis to middleware only. Compare today's behavior against yesterday's middleware diff and exclude build/runtime."
   EFFECT   Better boundary control. It closes off nearby branches the model would otherwise wander into.

2. INPUT    "Do not refactor unrelated modules. I only want the smallest change that restores production behavior."
   PATCH    "Give me the smallest safe patch. No refactors, no naming cleanup, and no unrelated file edits."
   EFFECT   Better output control. It specifies the acceptable shape of the answer, not just the general preference.

[NEXT DRILL]
Add one explicit acceptance rule to every corrective follow-up. Do not only narrow scope. State what the answer must include before the model writes it.

[RECENT TREND]
2026-04-10   score 6.8   weakest=Output Specification
2026-04-12   score 7.1   weakest=Context Provision
2026-04-13   score 7.4   weakest=Output Specification

[FOCUS AREA]
Output Specification is still the system bottleneck across recent sessions. Tighten the finish line earlier, then restate it every time you correct course.
```
