# Sample Rewrite Last Output

## Rewrite Last

**What Changed**

- tightened task scope
- made output shape explicit
- added a verification rule

**Rewrites**

1. Original: "Please review the failing deploy flow. First isolate whether the regression is in build, runtime, or auth middleware. Then propose the minimum fix and list the files you would touch."
   Rewrite: "Review the failing deploy flow and isolate the regression to exactly one layer: build, runtime, or auth middleware. Then propose the minimum safe fix, list the files you would touch, and say how you would verify the fix before shipping."
   Why: Adds a concrete verification requirement instead of ending at diagnosis.

2. Original: "Do not refactor unrelated modules. I only want the smallest change that restores production behavior."
   Rewrite: "Do not refactor unrelated modules. I want the smallest patch that restores production behavior, plus one sentence explaining why it is safer than broader cleanup."
   Why: Keeps the scope narrow while forcing a sharper decision standard.

3. Original: "That diagnosis is too broad. Narrow it to the middleware path only and compare against yesterday's behavior."
   Rewrite: "Limit the analysis to the middleware path only. Compare today's behavior against yesterday's middleware diff, exclude build/runtime, and tell me what evidence would confirm the bug is actually in middleware."
   Why: Converts a narrowing request into a falsifiable debugging instruction.

**Reusable Pattern**

```text
Focus on [scope only]. Give me [output shape]. Exclude [disallowed areas]. Before you finish, say how the result should be checked or falsified.
```
