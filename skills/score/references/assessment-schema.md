# Assessment Schema

Build an assessment object with these keys before calling the helper:

- `date`
- `plugin_version`
- `tool`
- `session_summary`
- `complexity`
- `meaningful_user_messages`
- `applicability`
- `evidence_counts`
- `dimensions`

## Field Notes

- `complexity`: `low | medium | high`
- `meaningful_user_messages`: count only user turns that materially steer the work
- `applicability.examples`: whether example usage was relevant in this session
- `applicability.reasoning`: whether reasoning elicitation was relevant in this session
- `applicability.tool_awareness`: whether tool usage was relevant in this session
- `dimensions.examples`: score or `null`
- `dimensions.reasoning`: score or `null`
- `dimensions.tool_awareness`: score or `null`

## Evidence Counts

Track these counts:

- `evidence_quotes`
- `corrections_or_refinements`
- `output_constraints`
- `tool_signals`

## Calibration

- Default to average unless the session proves more
- Do not score above `7` without direct evidence
- Do not treat session length as quality
- Do not reward vague but enthusiastic prompting
- Penalize weak output control and weak refinement discipline
