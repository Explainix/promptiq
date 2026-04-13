---
name: promptiq-install
description: Install PromptIQ and its local helper files for Claude Code, Codex CLI, or similar AI CLIs that use Markdown skill files. Use when the user runs /install or asks to set up PromptIQ on the current machine.
---

# Install PromptIQ

Install PromptIQ immediately. Do not ask follow-up questions unless a command fails.

1. Preserve user overrides when they are already set.
   Respect:
   - `PROMPTIQ_HOME` for helper, rubric, and history files
   - `CODEX_HOME` for Codex skill installation
   - `PROMPTIQ_SKIP_CODEX=1` to skip Codex installation
   - `PROMPTIQ_SKIP_CLAUDE=1` to skip Claude installation

2. Prefer the remote installer because this skill may be loaded from a raw URL.
   Run:

```bash
curl -fsSL -o /tmp/install_promptiq.py \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/install/scripts/install_promptiq.py
python3 /tmp/install_promptiq.py
```

3. If the remote installer cannot be downloaded but the repository exists locally, run:

```bash
python3 skills/install/scripts/install_promptiq.py
```

4. Fall back to manual install only if both installer paths fail.
   Manual install means:
   - install `~/.promptiq/promptiq.py`
   - install `~/.promptiq/rubric_v1.json`
   - install the full `promptiq` Codex skill bundle, including `references/`
   - install the `promptiq-install` skill bundle for Codex so reinstall/update flows still work
   - install the `promptiq-rewrite-last` skill bundle for Codex so users can improve recent prompts immediately
   - install the Claude plugin if `claude` is present and PromptIQ is not already available

5. Verify Python 3.
   Warn if `python3` is missing because deterministic scoring and history persistence will not work.

6. Report the result.
   Show `Trigger`, `Helper`, `Rubric`, `History`, `Verify`, and which CLI integrations were installed.
