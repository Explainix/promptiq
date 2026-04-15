---
name: promptiq
description: Strictly review the user's AI collaboration quality for the current session and render an evidence-based coaching report. Use when the user runs /score, asks for a hard review of their prompting, or wants calibrated feedback on how they collaborated with AI in this session.
---

# PromptIQ Review

Review only user messages. Evaluate the user's steering quality, not the assistant's quality.

1. Build a strict assessment for the current session.
   Score the 8 dimensions conservatively.
   Mark `examples`, `reasoning`, and `tool_awareness` as `null` when they are not applicable.
   Set `applicability.verification` to `true` when the task outcome should have been checked, tested, or otherwise verified.
   If the environment exposes a stable conversation or session identifier, include it as `session_id`.
   If the model/runtime version is known, include it as `model_version`.
   Keep high scores rare:
   - `5` = average
   - `6` = decent
   - `7` = clearly above average with evidence
   - `8` = strong power-user behavior
   - `9-10` = rare expert behavior
   Read [references/assessment-schema.md](references/assessment-schema.md) for the required assessment keys and field meanings.

2. Use the local helper.
   Respect `PROMPTIQ_HOME` when it is set. Otherwise use `~/.promptiq`.
   Check the resolved helper directory for `promptiq.py` and `rubric_v1.json`.
   If either file is missing, stop and tell the user to run `/install`.
   Write the assessment JSON to `/tmp/promptiq-assessment.json`.
   Run:

```bash
"${PROMPTIQ_HOME:-$HOME/.promptiq}/promptiq" finalize \
  --assessment-file /tmp/promptiq-assessment.json \
  --save
```

3. Treat helper output as the source of truth.
   Use helper output for `total`, `raw_total`, `confidence`, `trend`, `cap_reasons`, `score_band`, `weakest_dimension`, `next_band`, `why_not_higher`, `recent_trend`, `focus_area`, `history_session_count`, and `history_write`.
   Do not recompute those fields in the report.
   If `history_warning` is present, tell the user their local trend history was reset because the saved history file was unreadable.

4. Render the report.
   Use the exact section order in [references/report-template.md](references/report-template.md).
   Front-load `Why It Is Not Higher`.
   Use `weakest_dimension` for the drill.
   If `history_session_count >= 2`, include `Recent Trend` and `Focus Area`.
   Keep the tone direct and fair. Add only light encouragement at the end, and only if the evidence supports it.
