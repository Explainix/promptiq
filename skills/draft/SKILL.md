---
name: promptiq-draft
description: Turn a prompt intent or rough draft into a strong, paste-ready prompt. Use when the user runs /draft, wants to write a better prompt before sending it, or wants to improve a prompt they've already written.
---

# PromptIQ Draft

Turn the user's intent or rough draft into a strong, paste-ready prompt.

1. Identify the input type.
   - **Intent**: the user describes what they want to accomplish in natural language, without a formed prompt. Example: "I want to ask AI to refactor this function and remove duplicate logic."
   - **Draft**: the user has already written a prompt and wants it strengthened. Example: "Please refactor the getUserData function to remove duplicate logic."
   Infer the type from the input. Do not ask the user to specify.

2. Analyze what is missing or weak.
   Check for each of the following — apply only what is relevant to this specific task:
   - **Task boundary**: is the scope clear and narrow, or vague and open-ended?
   - **Context**: is there missing information the model would have to guess (file path, error message, current state, relevant constraints)?
   - **Output format**: does the prompt specify what the answer should look like?
   - **Verification condition**: does the prompt say how the user will know the answer is correct?
   - **Exclusions**: are there things the model should not do that are not stated?

3. Build the strengthened prompt.
   Preserve the user's intent and voice. Do not change the goal.
   Add only what is missing. Do not pad with unnecessary constraints.
   If verification is relevant to the task, the prompt must include how the result should be checked.

4. Render the result using the exact shape in [references/output-template.md](references/output-template.md).
   The prompt must be paste-ready immediately.
   Each "What changed" line must name a specific addition, not a vague theme.
