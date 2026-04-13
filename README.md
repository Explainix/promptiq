# PromptIQ

Strict session reviews for power users collaborating with AI.

PromptIQ reviews one session at a time. It does not claim to measure your permanent AI proficiency. It scores how well you steered the AI in the current session, explains why the score is not higher, and tracks trends only when sessions are compatible with the same rubric generation.

## What It Does

Run `/score` at the end of a session to get:

- A strict review across 8 collaboration dimensions
- A deterministic total with caps for weak evidence and low-complexity sessions
- Confidence and complexity labels beside the score
- A blunt "why it is not higher" explanation
- Recent compatible-session trend tracking for repeat users
- A next-session drill

## Product Positioning

PromptIQ is:

- A strict AI collaboration coach
- For high-frequency AI CLI users
- Focused on session quality, not vague long-term "proficiency"

This matters because a session review can be calibrated. A generic proficiency claim cannot.

## Repository Shape

```text
promptiq/
  README.md
  examples/
  package.json
  .claude-plugin/
  skills/
    score/SKILL.md
    score/references/
    install/SKILL.md
    install/scripts/install_promptiq.py
  engine/
    promptiq.py
    rubric_v1.json
  fixtures/
  tests/
```

## Installation

### Quick Start

Recommended bootstrap:

```bash
curl -fsSL -o /tmp/install_promptiq.py \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/install/scripts/install_promptiq.py
python3 /tmp/install_promptiq.py
```

This installs:

- `~/.promptiq/promptiq.py`
- `~/.promptiq/rubric_v1.json`
- the `promptiq` Codex skill bundle when `codex` is present
- the Claude plugin when `claude` is present

### Agent-driven install

Ask your AI CLI to download and run:

```text
https://raw.githubusercontent.com/Explainix/promptiq/main/skills/install/scripts/install_promptiq.py
```

### Claude Code

1. Install the plugin:

```bash
claude plugin marketplace add Explainix/promptiq
claude plugin install promptiq
```

2. Run `/install` once to place the local helper in `~/.promptiq/`.

### Codex CLI

The quick-start installer above is recommended.

Manual fallback:

```bash
python3 /tmp/install_promptiq.py
```

Restart Codex after installing the skill.

## Usage

- Run `/score` after a real working session, not a trivial one-liner.
- If `~/.promptiq/promptiq.py` is missing, run `/install` first.

## Example Output

See [examples/sample-report.md](examples/sample-report.md) for a representative review.

## How Scoring Works

The model still judges the session. The local helper makes the system stricter and more stable by handling:

- N/A filtering
- total calculation
- score caps
- confidence calculation
- rubric-compatible trend tracking
- long-term focus-area detection

The helper also supports file-based assessment input so large session payloads do not break on shell escaping.

## Calibration Rules

- Short sessions are capped
- Low-complexity sessions are capped
- Low-confidence sessions are capped
- Scores above 7.5 require evidence
- Scores above 8.5 are intentionally rare

## Privacy

PromptIQ stores history locally at `~/.promptiq/history.json`. Nothing is uploaded by PromptIQ itself.
