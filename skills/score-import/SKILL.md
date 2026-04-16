---
name: promptiq-score-import
description: Review an imported PromptIQ session transcript and render the same strict coaching report used by /score. Use when the user runs /score-import, asks to review a past imported session, or wants PromptIQ to score an imported transcript.
---

# PromptIQ Score Import

Review only user messages from the imported session. Evaluate steering quality, not assistant quality.

1. Resolve the imported session to score.
   The engine is bundled at `skills/score-import/scripts/promptiq.py`.
   Run:

```bash
python skills/score-import/scripts/promptiq.py list-imports
```

   If there are no imported sessions, stop and tell the user to run `import-session` first.
   If the user named a specific `session_id`, use it.
   Otherwise score the most recently imported session.

2. Prepare the imported review workspace.
   If you are scoring the most recent import, run:

```bash
python skills/score-import/scripts/promptiq.py score-import
```

   If you are scoring a specific imported session, run:

```bash
python skills/score-import/scripts/promptiq.py score-import \
  --session-id [target-session-id]
```

   Use the returned `assessment_file` and `replay_file`.
   The helper already writes the assessment seed to `assessment_file` and the user-only transcript replay to `replay_file`.
   Keep the provided `session_id`, `session_fingerprint`, `tool`, `model_version`, and `meaningful_user_messages` unless the transcript proves they should change.
   Fill in `complexity`, `applicability`, `evidence_counts`, and `dimensions` conservatively.
   Read [references/assessment-schema.md](references/assessment-schema.md) for the required field meanings.

3. Finalize the score through the local helper.
   Edit `assessment_file` in place, then run the returned `next_command`.
   Run:

```bash
[next_command from score-import]
```

4. Render the report.
   Use the exact shape in [references/output-template.md](references/output-template.md).
   Keep the tone direct, fair, and technical.
   Mention which imported session was reviewed before the main report using a single-line preface.
