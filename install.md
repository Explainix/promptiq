# PromptIQ — Install Instructions

Follow these steps to install PromptIQ.

## Claude Code

Run these three commands inside a Claude Code session:

```
/plugin marketplace add Explainix/promptiq
/plugin install promptiq@explainix
/reload-plugins
```

PromptIQ is now active. Type `/score` at the end of any session to get your review. Type `/draft` before sending a prompt to strengthen it first.

## Codex

Run this in your terminal:

```bash
git clone https://github.com/Explainix/promptiq ~/.codex/skills/promptiq
```

Then type `/score` at the end of any session.

---

No account required. History is stored locally at `~/.promptiq/history.json`.
