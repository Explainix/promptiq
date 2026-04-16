# Sample Draft Output

## Example 1 — Intent input

User input: "I want to ask AI to find all the places in the codebase where we're not handling errors properly"

## Draft

**Prompt**

Search the codebase for async functions that call external APIs or database queries without a try/catch block. List each file path and line number. Do not suggest fixes — only identify the locations. When done, tell me how many you found and whether any are in critical paths (auth, payments, data writes).

**What changed**

- Narrowed scope to async functions with external calls — removes ambiguity about what "not handling errors" means
- Added output format — file path and line number list, not prose
- Added exclusion — no fixes, identification only
- Added verification condition — count and critical path flag so the result can be assessed

---

## Example 2 — Draft input

User input: "Please refactor the getUserData function to remove duplicate logic"

## Draft

**Prompt**

Refactor the `getUserData` function to remove duplicate logic. Do not change the function's public interface or rename it. Do not touch any other functions. When done, show me the before and after side by side and explain what was duplicated.

**What changed**

- Added interface constraint — public signature must stay the same
- Added exclusion — no other functions touched
- Added output format — before/after comparison with explanation

**Pattern**

```text
Refactor [function/module] to [specific goal]. Do not change [interface/other files]. When done, show [output format] and explain [what changed and why].
```
