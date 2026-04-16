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
   For each dimension you score above 5, write a one-sentence evidence string that quotes or paraphrases the specific user prompt behavior that drove the score. Store these in an `evidence` dict keyed by dimension name.
   Example: `"evidence": {"clarity": "Third prompt did not specify expected output format", "context": "Provided file path and error message at session start"}`
   If you cannot find specific evidence for a dimension score above 5, lower the score to 5 instead of inventing evidence.

2. Use the local helper.
   The engine is bundled at `skills/score/scripts/promptiq.py`.
   Write the assessment JSON to `/tmp/promptiq-assessment.json`.
   Run:

```bash
python skills/score/scripts/promptiq.py finalize \
  --assessment-file /tmp/promptiq-assessment.json \
  --save
```

3. Treat helper output as the source of truth.
   Use helper output for `total`, `raw_total`, `confidence`, `trend`, `cap_reasons`, `score_band`, `weakest_dimension`, `next_band`, `why_not_higher`, `recent_trend`, `focus_area`, `history_session_count`, and `history_write`.
   Do not recompute those fields in the report.
   If `history_warning` is present, tell the user their local trend history was reset because the saved history file was unreadable.

4. Detect the user's language.
   Check the language of the user's messages in this session.
   If the majority of user messages are in Chinese (Simplified or Traditional), render the report in Chinese using [references/report-template.zh.md](references/report-template.zh.md).
   Otherwise, render in English using [references/report-template.md](references/report-template.md).

5. Render the report.
   Use the exact section order in the chosen template.
   Front-load `Why It Is Not Higher`.
   Use `weakest_dimension` as the Focus Dimension with its evidence sentence from the assessment.
   Fold all other dimensions into the compact bar list.
   If `history_session_count >= 2`, include `Recent Trend` and `Focus Area`.
   If `milestone` is present, include the `Milestone` section.
   End with the `Next Step` offer: rewrite offer if `weakest_dimension.score < 6`, drill suggestion otherwise.
   Keep the tone direct and fair.
