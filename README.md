# PromptIQ

Strict session reviews for power users collaborating with AI.

PromptIQ does not claim to measure your permanent AI proficiency. It reviews one working session at a time, scores how well you steered the model, explains why the score is not higher, and stores comparable history only when the rubric generation matches.

## Why This Exists

High-frequency AI CLI users usually do not need more inspiration. They need sharper feedback on habits that actually change outcomes:

- Was the request scoped tightly enough?
- Was the relevant context supplied early?
- Were weak answers corrected instead of accepted?
- Were output constraints explicit enough to verify success?
- Did the user define how the answer would be checked, tested, or falsified?
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

Run `/rewrite-last` when you want PromptIQ to rewrite your last 1-3 meaningful prompts into stronger, paste-ready versions for the same task.

Run `/score-import` when you want PromptIQ to review a previously imported session instead of the live thread.

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

```bash
git clone https://github.com/Explainix/promptiq ~/.claude/skills/promptiq
```

Then type `/score` in Claude Code.

### Verify

```bash
python ~/.claude/skills/promptiq/skills/score/scripts/promptiq.py doctor
```

## Usage

1. Work through a real session.
2. Run `/score`.
3. Read `Why It Is Not Higher` before looking at the total.
4. Apply the `Next Session Drill` in your next working session.
5. Run `/rewrite-last` when you want PromptIQ to tighten your recent prompts immediately.

## Import Past Sessions

PromptIQ can also normalize and store old session transcripts locally so we can build replay and backfill workflows on top of stable data instead of brittle copy-paste.

Import a session file:

```bash
python ~/.claude/skills/promptiq/skills/score/scripts/promptiq.py import-session \
  --session-file ./fixtures/structured_debug_session.json
```

List imported sessions:

```bash
python ~/.claude/skills/promptiq/skills/score/scripts/promptiq.py list-imports
```

Replay one imported session as a clean review artifact:

```bash
python ~/.claude/skills/promptiq/skills/score/scripts/promptiq.py replay-session --format markdown
```

Include assistant turns when you need the full exchange instead of PromptIQ's default user-only view:

```bash
python ~/.claude/skills/promptiq/skills/score/scripts/promptiq.py replay-session \
  --include-assistant \
  --format markdown
```

Add `--session-id [id]` when you want a specific imported session instead of the most recent one.

Supported JSON input shapes:

- fixture-style objects with `transcript`
- session objects with `messages`
- raw arrays of `{role, content}` messages

The default replay view shows only user turns because PromptIQ scores steering quality, not assistant quality.

PromptIQ stores imported bundles locally at `~/.promptiq/imports/` unless `PROMPTIQ_HOME` or `PROMPTIQ_IMPORTS_PATH` says otherwise.

If you want to turn an imported session into a real PromptIQ review workflow, generate an assessment seed first:

```bash
python ~/.claude/skills/promptiq/skills/score/scripts/promptiq.py score-import
```

That command writes a ready-to-edit assessment JSON and a replay markdown file for the most recent imported session, then returns the exact finalize command to run after you fill in the judgment fields.
Add `--session-id [id]` when you want to score a specific imported session instead of the latest one.

## What Strong Sessions Usually Look Like

PromptIQ is designed around patterns strong AI CLI users repeat consistently:

- one concrete task at a time
- relevant repo or business context up front
- explicit success criteria or output format
- an explicit way to verify whether the answer is actually correct
- corrective follow-ups when the first answer drifts
- tool use when the task benefits from search, tests, logs, or docs

This matters because long sessions with vague prompts often feel productive while actually producing weak steering. PromptIQ is intentionally strict about that difference.

## Example Output

See [examples/sample-report.md](examples/sample-report.md) for a representative report.
See [examples/imported-report-sample.md](examples/imported-report-sample.md) for a representative `/score-import` report.
See [examples/rewrite-last-sample.md](examples/rewrite-last-sample.md) for a representative `/rewrite-last` result.

Together, these examples act as the repo's golden output contracts for live review, imported review, and prompt rewrite flows.

## How Scoring Works

The model still judges the session. The local helper makes the product stricter and more stable by handling:

- N/A filtering
- total calculation
- score caps
- confidence determination
- rubric-compatible trend tracking
- long-term focus-area detection
- verification-aware high-score gating

The helper also supports file-based assessment input so large session payloads do not break on shell escaping.

## Calibration Rules

- short sessions are capped
- low-complexity sessions are capped
- low-confidence sessions are capped
- scores above `7.5` require evidence
- scores above `8.5` are intentionally rare

## Privacy

PromptIQ stores history locally at `~/.promptiq/history.json` and imported transcript bundles at `~/.promptiq/imports/` unless `PROMPTIQ_HOME`, `PROMPTIQ_HISTORY_PATH`, or `PROMPTIQ_IMPORTS_PATH` says otherwise. PromptIQ does not upload that data by itself.

## Local Development

```bash
python3 -m unittest discover -s tests -v
python ~/.claude/skills/promptiq/skills/score/scripts/promptiq.py doctor
```

If you change calibration or report behavior, update fixtures and tests in the same pull request.

## Repo Layout

```text
promptiq/
  examples/
  fixtures/
  skills/
  tests/
```

## Related Docs

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [docs/user-research.md](docs/user-research.md)
