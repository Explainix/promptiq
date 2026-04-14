# Contributing to PromptIQ

PromptIQ is a small repo, but it is opinionated. The goal is not to ship more surface area. The goal is to make `/score` more trustworthy and more useful for serious AI CLI users.

## Product Principles

- Trust beats warmth.
- Evidence beats vibes.
- Coaching beats compliments.
- Session review is a narrower claim than long-term proficiency, and we should keep it that way.
- High scores should stay rare.

## Local Setup

```bash
python3 -m unittest discover -s tests -v
python3 engine/promptiq.py doctor
```

The repo intentionally avoids heavy dependencies. Please keep it lightweight unless a change clearly improves user trust or contributor velocity.

## What Good Contributions Look Like

Useful contributions usually strengthen one of these areas:

- stricter and more stable scoring behavior
- clearer installation and troubleshooting
- sturdier transcript import compatibility for replay and backfill workflows
- better explanation of what PromptIQ is and is not
- fixture-driven calibration protection
- contributor experience for testing and validating changes

## Calibration Changes

If you change scoring, confidence, history, or report logic:

- add or update tests in `tests/`
- update relevant fixtures in `fixtures/` when expectations change
- update example outputs when the output contract changes
- explain why the stricter behavior is better for real users
- avoid making the product more flattering unless there is strong evidence it also becomes more accurate

PromptIQ should not drift into a compliment engine.

## Transcript Import Changes

If you change transcript import or normalization behavior:

- add tests for each accepted payload shape you support
- add at least one malformed-payload test when broadening compatibility
- preserve local-only storage unless there is an explicit product decision to change it

## Fixture Guidance

Fixtures should represent real collaboration patterns, not synthetic perfection. The baseline set should always include:

- short simple sessions
- verbose but weakly steered sessions
- strong debugging or implementation sessions
- rare elite sessions with dense evidence

## Documentation

When changing README or docs:

- make the first screen answer "who is this for?" and "how do I verify it worked?"
- prefer concrete examples over abstract claims
- preserve the difference between session review and general prompt proficiency

## Output Contracts

PromptIQ treats the example markdown files as golden output contracts:

- `examples/sample-report.md`
- `examples/imported-report-sample.md`
- `examples/rewrite-last-sample.md`

If you change output structure, headings, or summary tables, update the matching templates and keep `tests/test_output_contracts.py` passing.

## Pull Requests

A good PR description should include:

- the user problem being addressed
- the change in behavior
- the verification steps you ran
- whether calibration expectations changed
