# Sample PromptIQ Imported Report

Reviewed imported session `import-b6026318c8a8` from `fixtures/structured_debug_session.json`.

## PromptIQ Review

| Metric | Value |
| --- | --- |
| Score | 7.4/10 |
| Band | competent |
| Confidence | medium |
| Complexity | high |
| Delta | +0.3 vs last compatible session |

**Why It Is Not Higher**  
This imported session shows real steering discipline, but the end-state is still not strict enough to clear the next band. The user scoped the investigation well and corrected drift quickly, yet they never made verification explicit enough to prove the patch would be correct before shipping.

**Dimension Breakdown**

```text
Instruction Clarity    ███████░░░  7/10
Context Provision      ███████░░░  7/10
Iteration Quality      ████████░░  8/10
Task Decomposition     ████████░░  8/10
Output Specification   ███████░░░  7/10
Example Usage          ──────────  N/A
Reasoning Elicitation  ████████░░  8/10
Tool Awareness         ███████░░░  7/10
```

**Strongest Evidence**

> "Please review the failing deploy flow. First isolate whether the regression is in build, runtime, or auth middleware. Then propose the minimum fix and list the files you would touch."

This imported prompt is strong because it constrains the order of analysis and the expected output before the model starts. It gives the session a crisp lane instead of a vague debugging brief.

**Course Corrections**

1. Input: "Do not refactor unrelated modules. I only want the smallest change that restores production behavior."  
   Patch: "Give me the smallest safe patch that restores production behavior. No refactors, no cleanup passes, and no unrelated file edits."  
   Effect: Better output control. It tightens what counts as an acceptable answer instead of leaving "smallest change" open to interpretation.

2. Input: "That diagnosis is too broad. Narrow it to the middleware path only and compare against yesterday's behavior."  
   Patch: "Limit the analysis to middleware only. Compare today's behavior against yesterday's middleware diff, exclude build/runtime, and tell me what evidence would confirm the regression is actually in middleware."  
   Effect: Better verification control. It turns a narrowing request into a falsifiable debugging instruction.

**Next Session Drill**  
When you narrow scope, add one concrete verification rule in the same turn. Do not only say what to exclude. Say what evidence would confirm the diagnosis or fix.

**Recent Trend**

| Date | Score | Weakest |
| --- | --- | --- |
| 2026-04-10 | 6.8 | Output Specification |
| 2026-04-12 | 7.1 | Context Provision |
| 2026-04-13 | 7.4 | Output Specification |

**Focus Area**  
Output Specification is still the long-running bottleneck, even in imported reviews. Tighten the finish line earlier and pair it with a concrete check so the result can be proven instead of assumed.
