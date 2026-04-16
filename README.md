# PromptIQ

[中文](README.zh.md) | English

Strict session reviews for power users collaborating with AI.

## What It Does

Run `/score` at the end of a working session to get:

- a strict review across 8 collaboration dimensions
- a deterministic total with caps for weak evidence and low-complexity sessions
- a blunt **Why It Is Not Higher** section
- one concrete next-session drill

Run `/draft` before sending a prompt — give it your intent or a rough draft, get back a stronger, paste-ready version with an explanation of what changed.

## Install

### Claude Code

```
/plugin marketplace add Explainix/promptiq
/plugin install promptiq@promptiq
/reload-plugins
```

Or from the terminal:

```bash
claude plugin install promptiq@promptiq
```

Then type `/score` at the end of any session.

### Codex

```bash
git clone https://github.com/Explainix/promptiq ~/.codex/skills/promptiq
```

Then type `/score` at the end of any session.

## Usage

1. Work through a real session.
2. Run `/score`.
3. Read **Why It Is Not Higher** before looking at the total.
4. Apply the **Next Session Drill** next time.
5. Run `/draft` before your next prompt to write it stronger from the start.

## Who It Is For

- Frequent Claude Code / Codex users who want sharper steering habits
- People who want calibrated feedback, not softer praise
- Anyone who suspects their prompts are vague but can't see where

Not for trivial one-liner sessions or generic personality tests.

## How Scoring Works

The local engine handles N/A filtering, total calculation, score caps, confidence, and trend tracking. The model judges the session — the engine makes the result strict and stable.

Calibration rules:
- short, low-complexity, or low-confidence sessions are capped
- scores above 7.5 require evidence
- scores above 8.5 are intentionally rare

## Example Output

- [examples/sample-report.md](examples/sample-report.md) — representative `/score` report
- [examples/draft-sample.md](examples/draft-sample.md) — representative `/draft` result

## Privacy

History is stored locally at `~/.promptiq/history.json`. PromptIQ does not upload it.

## Local Development

```bash
python3 -m unittest discover -s tests -v
python skills/score/scripts/promptiq.py doctor
```

## License

MIT
