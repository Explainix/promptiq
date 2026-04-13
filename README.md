# PromptIQ

Strict session reviews for power users collaborating with AI.

PromptIQ does not claim to measure your permanent AI proficiency. It reviews one working session at a time, scores how well you steered the model, explains why the score is not higher, and stores comparable history only when the rubric generation matches.

## Why This Exists

High-frequency AI CLI users usually do not need more inspiration. They need sharper feedback on habits that actually change outcomes:

- Was the request scoped tightly enough?
- Was the relevant context supplied early?
- Were weak answers corrected instead of accepted?
- Were output constraints explicit enough to verify success?
- Were tools and AI-native workflows used when they mattered?

PromptIQ is built to coach those habits directly.

## What You Get

Run `/score` at the end of a real session to get:

- a strict review across 8 collaboration dimensions
- a deterministic total with caps for weak evidence and low-complexity sessions
- confidence and complexity labels beside the score
- a blunt `Why It Is Not Higher` section
- compatible-session trend tracking for repeat users
- one next-session drill instead of a pile of generic advice

## Who It Is For

PromptIQ is for users who:

- use Codex, Claude Code, or similar AI CLIs frequently
- want sharper steering, not softer praise
- care about repeatable prompting habits more than one-off clever prompts

PromptIQ is not for:

- trivial one-liner sessions
- people looking for a generic personality test
- teams that want full prompt regression testing across models and datasets

## Quick Start

### AI-native install

Paste this into your AI CLI:

```text
Read https://raw.githubusercontent.com/Explainix/promptiq/main/skills/install/SKILL.md and install PromptIQ. Do not ask follow-up questions unless a command fails.
```

### Shell install

```bash
curl -fsSL -o /tmp/install_promptiq.py \
  https://raw.githubusercontent.com/Explainix/promptiq/main/skills/install/scripts/install_promptiq.py
python3 /tmp/install_promptiq.py
```

### Verify the install

```bash
python3 "${PROMPTIQ_HOME:-$HOME/.promptiq}/promptiq.py" doctor
```

The `doctor` command tells you:

- where PromptIQ is installed
- whether the helper and rubric are present
- where history will be stored
- how many local sessions are currently tracked
- whether your local history is corrupted and needs to be recreated

## Usage

1. Work through a real session.
2. Run `/score`.
3. Read `Why It Is Not Higher` before looking at the total.
4. Apply the `Next Session Drill` in your next working session.

If `promptiq.py` or `rubric_v1.json` is missing, run `/install` first.

## What Strong Sessions Usually Look Like

PromptIQ is designed around patterns strong AI CLI users repeat consistently:

- one concrete task at a time
- relevant repo or business context up front
- explicit success criteria or output format
- corrective follow-ups when the first answer drifts
- tool use when the task benefits from search, tests, logs, or docs

This matters because long sessions with vague prompts often feel productive while actually producing weak steering. PromptIQ is intentionally strict about that difference.

## Example Output

See [examples/sample-report.md](examples/sample-report.md) for a representative report.

## How Scoring Works

The model still judges the session. The local helper makes the product stricter and more stable by handling:

- N/A filtering
- total calculation
- score caps
- confidence determination
- rubric-compatible trend tracking
- long-term focus-area detection

The helper also supports file-based assessment input so large session payloads do not break on shell escaping.

## Calibration Rules

- short sessions are capped
- low-complexity sessions are capped
- low-confidence sessions are capped
- scores above `7.5` require evidence
- scores above `8.5` are intentionally rare

## Privacy

PromptIQ stores history locally at `~/.promptiq/history.json` unless `PROMPTIQ_HOME` or `PROMPTIQ_HISTORY_PATH` says otherwise. PromptIQ does not upload that history by itself.

## Local Development

```bash
python3 -m unittest discover -s tests -v
python3 engine/promptiq.py doctor
```

If you change calibration or report behavior, update fixtures and tests in the same pull request.

## Repo Layout

```text
promptiq/
  engine/
  examples/
  fixtures/
  skills/
  tests/
```

## Related Docs

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [docs/user-research.md](docs/user-research.md)
