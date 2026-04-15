---
name: promptiq-rewrite-last
description: Rewrite the user's last 1-3 meaningful prompts into stronger versions for the same task. Use when the user runs /rewrite-last, asks to improve their recent prompt, or wants a sharper version of what they just asked the AI to do.
---

# PromptIQ Rewrite Last

Rewrite only the user's recent prompts. Do not review or rewrite assistant messages.

1. Identify the last 1-3 meaningful user prompts in the current session.
   Ignore filler like "continue", "ok", or "do it".
   If only one prompt is meaningful, rewrite one.

   **If triggered from a `/score` report** (the user said yes to the rewrite offer):
   The target prompt is the one that drove the weakest dimension score.
   Use the evidence sentence from the assessment to frame the rewrite:
   - Show the original prompt
   - Show the evidence sentence explaining why it was weak
   - Show the rewritten version
   - Show what specifically changed and why

   Format:
   **Original**
   > [original prompt text]

   **Why it was weak**
   [evidence sentence]

   **Rewritten**
   > [improved prompt]

   **What changed**
   [2-3 bullet points: specific additions or changes made]

2. Preserve intent.
   Do not change the user's goal.
   Tighten scope, context, constraints, output shape, and verification plan.

3. Improve the prompts using PromptIQ standards.
   Strong rewrites usually add:
   - a tighter task boundary
   - missing context the model would otherwise have to guess
   - explicit output requirements
   - at least one verification or acceptance rule when the task should be checked

4. Render the result using the exact shape in [references/output-template.md](references/output-template.md).
   Keep it concise and practical.
   The rewritten prompts should be ready to paste into a live session immediately.
