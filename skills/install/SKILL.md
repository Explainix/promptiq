---
name: promptiq-install
description: Install PromptIQ and its local helper files for Claude Code, Codex CLI, or similar AI CLIs that use Markdown skill files. Use when the user runs /install or asks to set up PromptIQ on the current machine.
---

# Install PromptIQ

1. Prefer the bundled installer.
   Read [scripts/install_promptiq.py](scripts/install_promptiq.py).
   If the script is available locally, run it.
   Otherwise fetch the raw installer script to `/tmp` and run that copy.
   The installer script is the source of truth.

```bash
python3 skills/install/scripts/install_promptiq.py
```

Remote fallback:

```bash
curl -fsSL -o /tmp/install_promptiq.py \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/install/scripts/install_promptiq.py
python3 /tmp/install_promptiq.py
```

2. Fall back only if the bundled installer cannot be used.
   Reproduce the same steps manually:
   - install `~/.promptiq/promptiq.py`
   - install `~/.promptiq/rubric_v1.json`
   - install the full `promptiq` skill bundle for Codex, including `references/`
   - install the `promptiq-install` skill bundle for Codex so reinstall/update flows still work
   - install the Claude plugin if `claude` is present and PromptIQ is not already available

3. Verify Python 3.
   Warn if `python3` is missing because deterministic scoring and history persistence will not work.

4. Report the result.
   Show `Trigger`, `Helper`, `Rubric`, `History`, and which CLI integrations were installed.
