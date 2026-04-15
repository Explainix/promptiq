# Assessment Schema

Build an assessment object with these keys before calling the helper:

- `date`
- `plugin_version`
- `session_id` (optional)
- `session_fingerprint` (optional)
- `model_version` (optional)
- `tool`
- `session_summary`
- `complexity`
- `meaningful_user_messages`
- `applicability`
- `evidence_counts`
- `dimensions`
- `evidence` (optional) — dict mapping dimension key to a one-sentence string quoting the specific prompt behavior that drove the score. Keys must match keys in `dimensions`. Example: `{"clarity": "Third prompt did not specify expected output format"}`

## Field Notes

- `complexity`: `low | medium | high`
- `session_id`: use when the runtime exposes a stable conversation or session identifier
- `session_fingerprint`: optional explicit fingerprint for the current session; if omitted, the helper derives a best-effort fingerprint from the assessment payload
- `model_version`: optional model identifier used for future trend analysis and debugging
- `meaningful_user_messages`: count only user turns that materially steer the work
- `applicability.examples`: whether example usage was relevant in this session
- `applicability.reasoning`: whether reasoning elicitation was relevant in this session
- `applicability.tool_awareness`: whether tool usage was relevant in this session
- `applicability.verification`: whether the task outcome should have been checked, tested, or otherwise falsified
- `dimensions.examples`: score or `null`
- `dimensions.reasoning`: score or `null`
- `dimensions.tool_awareness`: score or `null`

## Evidence Counts

Track these counts:

- `evidence_quotes`
- `corrections_or_refinements`
- `output_constraints`
- `tool_signals`
- `verification_signals`

## Calibration

- Default to average unless the session proves more
- Do not score above `7` without direct evidence
- Do not treat session length as quality
- Do not reward vague but enthusiastic prompting
- Penalize weak output control and weak refinement discipline
- When verification is relevant, penalize sessions that never define how success will be checked
