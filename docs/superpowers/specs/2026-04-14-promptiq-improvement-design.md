# PromptIQ Improvement Design

Date: 2026-04-14
Status: Approved

## Product Diagnosis

PromptIQ is currently a **diagnostic tool** — it scores a session and stops. The core problem is that diagnosis without a feedback loop does not change behavior. Users need a **habit system** that is embedded in their workflow, not a report they read once and forget.

### Root Problems

**P1 — Report ends the experience**
`/score` outputs a report and stops. "Next Session Drill" is static text. There is no mechanism that connects the diagnosis to the next action. `/rewrite-last` exists but is a disconnected island — users do not know when to use it or how it relates to their score.

**P2 — Scores lack verifiable evidence**
A score of 7.2 carries no authority when the user cannot see why it is not 7.5. The current report attributes scores to dimensions but does not quote the specific prompt behavior that drove each score. Users cannot verify the judgment, so they do not trust it.

**P3 — 8 dimensions create cognitive overload**
Every report surfaces all 8 dimensions equally. Users cannot act on 8 things at once. The report reads as information-dense rather than action-clear.

**P4 — Trend is a footnote, not the core value**
Trend tracking only appears after 3 sessions and is a minor section. But trend is the highest-value output of the product — it is the only thing that proves the user is improving. It should be the headline, not a footnote.

---

## Improvement Specification

### Improvement 1: Evidence Sentences Per Dimension (P0)

Every dimension score must be accompanied by a one-sentence evidence quote from the actual session.

**Format:**
```
clarity: 6  — "Third prompt did not specify expected output format"
context: 8  — "Provided file path and error message at session start"
```

**Rules:**
- Evidence sentence must reference a specific prompt or behavior, not a general observation
- If no evidence can be found for a dimension, the score must be capped at 5 (neutral)
- Evidence sentences go in the assessment JSON under `evidence` per dimension
- The report template renders them inline beside each score

**Why this matters:** Transforms scores from model opinions into verifiable observations. Users can agree or disagree with specific evidence, which builds trust in the system.

---

### Improvement 2: Report Becomes a Conversation Starter (P0)

The report must not end with static text. After the "Next Session Drill", the report offers one concrete next action the user can take immediately.

**Logic:**
- If the weakest dimension score < 6: offer to rewrite the weakest prompt from this session
- If the weakest dimension score >= 6: offer a focused drill question for next session

**Offer format (weakest < 6):**
```
Your [dimension] score was [N]. Want me to rewrite your weakest prompt from this session to show what a stronger version looks like?
```

**Offer format (weakest >= 6):**
```
Next session, try this: [one specific constraint to add to your prompts based on weakest dimension]
```

**Rules:**
- Only one offer, never two
- The offer must be actionable in under 30 seconds
- If user says yes to rewrite, trigger the equivalent of `/rewrite-last` targeting the specific weak prompt

---

### Improvement 3: Focus on 1 Dimension, Fold the Rest (P1)

The report must lead with the single most important dimension to improve, not a flat list of 8.

**Report structure change:**
1. Total score + band + confidence (unchanged)
2. Why It Is Not Higher (unchanged, but now references the focus dimension)
3. **Focus Dimension** — full breakdown with evidence, score, and what good looks like
4. **Other Dimensions** — collapsed summary (name + score only, one line each)
5. Next Session Drill (unchanged)
6. Conversation offer (new, from Improvement 2)

**Rules:**
- Focus dimension = `weakest_dimension` from the engine output
- "Other Dimensions" section uses a compact format, not the full breakdown
- Users who want detail on other dimensions can ask

---

### Improvement 4: Trend as Core Narrative (P1)

Trend tracking must start at session 2, not session 3. The trend section must tell a story, not just show numbers.

**Changes:**
- Show trend from session 2 onward (currently session 3)
- Trend narrative format:

```
Your [dimension] has been your strongest area for [N] sessions.
Your [dimension] dropped this session — you scored [N] vs [N] last time.
```

- Add milestone messages at sessions 5, 10, 20:

```
10 sessions in. Your average has moved from [N] to [N].
Strongest growth: [dimension]. Still needs work: [dimension].
```

**Engine changes needed:**
- `recent_trend` must include per-dimension deltas, not just total delta
- History must store `weakest_dimension` per session for trend analysis
- Milestone detection logic in `promptiq.py`

---

### Improvement 5: `/rewrite-last` Integration (P0, part of Improvement 2)

`/rewrite-last` must be triggerable from within a `/score` report flow, not only as a standalone command.

**When triggered from `/score`:**
- Target the specific prompt that drove the weakest dimension score
- The rewrite must reference the evidence sentence from the assessment
- Output format is the same as standalone `/rewrite-last`

**Standalone `/rewrite-last` is unchanged** — it still rewrites the last 1-3 meaningful prompts without needing a prior `/score`.

---

## Priority Order

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| P0 | Evidence sentences per dimension | Medium | High — fixes trust problem |
| P0 | Report → conversation starter + rewrite integration | Low | High — fixes retention problem |
| P1 | Focus on 1 dimension, fold the rest | Low | Medium — fixes cognitive load |
| P1 | Trend from session 2 + narrative format | Medium | High — fixes core value prop |

---

## Files Affected

| File | Change |
|------|--------|
| `engine/promptiq.py` | Add `evidence` field per dimension; add per-dimension trend deltas; add milestone detection; lower trend threshold to 2 sessions |
| `engine/rubric_v1.json` | Add evidence requirement rule; no-evidence cap at 5 |
| `skills/score/SKILL.md` | Require evidence sentences in assessment; update report rendering instructions |
| `skills/score/references/assessment-schema.md` | Add `evidence` field to schema |
| `skills/score/references/report-template.md` | New report structure: focus dimension + folded others + conversation offer |
| `skills/rewrite-last/SKILL.md` | Add "triggered from score" mode with target prompt context |

---

## Success Criteria

1. Every dimension score in a report has a one-sentence evidence quote
2. Every report ends with one actionable offer (rewrite or drill)
3. Trend appears from session 2 onward
4. Report structure leads with focus dimension, not a flat 8-dimension list
5. A user reading the report for the first time knows exactly what to do next
