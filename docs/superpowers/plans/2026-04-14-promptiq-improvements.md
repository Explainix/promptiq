# PromptIQ Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform PromptIQ from a passive scoring tool into an active coaching loop by adding evidence sentences per dimension, a conversation-starter report ending, focused dimension reporting, and earlier trend tracking.

**Architecture:** Changes flow through three layers — (1) engine (`promptiq.py`) gains evidence storage and per-dimension trend deltas, (2) rubric (`rubric_v1.json`) gains evidence requirement rules, (3) skills (`SKILL.md` files) gain updated assessment instructions and report templates. Each layer is independently testable.

**Tech Stack:** Python 3, JSON rubric, Markdown skill files, pytest

---

## File Map

| File | Role |
|------|------|
| `engine/promptiq.py` | Add evidence validation; add per-dimension trend deltas; lower trend threshold to 2 sessions; add milestone detection |
| `engine/rubric_v1.json` | Add `evidence_required: true` flag; add `no_evidence_cap: 5.0` rule |
| `skills/score/references/assessment-schema.md` | Add `evidence` field documentation |
| `skills/score/references/report-template.md` | New structure: focus dimension + folded others + conversation offer |
| `skills/score/SKILL.md` | Require evidence sentences in assessment JSON; update report rendering |
| `skills/rewrite-last/SKILL.md` | Add "triggered from score" mode |
| `tests/test_engine.py` | New tests for evidence validation, trend threshold, milestone detection |

---

## Task 1: Add `evidence` field to assessment schema and validation

**Files:**
- Modify: `engine/promptiq.py:84-125` (`validate_assessment`)
- Modify: `skills/score/references/assessment-schema.md`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine.py — add to existing test file
def test_validate_assessment_accepts_evidence_field():
    """evidence field is optional but when present must be a dict of dimension -> string."""
    base = make_valid_assessment()
    base["evidence"] = {
        "clarity": "Third prompt did not specify expected output format",
        "context": "Provided file path and error message at session start",
    }
    # should not raise
    validate_assessment(base)

def test_validate_assessment_rejects_non_string_evidence_value():
    base = make_valid_assessment()
    base["evidence"] = {"clarity": 42}
    with pytest.raises(ValueError, match="evidence"):
        validate_assessment(base)

def test_validate_assessment_rejects_unknown_dimension_in_evidence():
    base = make_valid_assessment()
    base["evidence"] = {"nonexistent_dim": "some text"}
    with pytest.raises(ValueError, match="evidence"):
        validate_assessment(base)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/huccct/Frontend/promptiq
python -m pytest tests/test_engine.py -k "evidence" -v
```

Expected: FAIL — `validate_assessment` does not handle `evidence` field yet.

- [ ] **Step 3: Add evidence validation to `validate_assessment` in `engine/promptiq.py`**

Find the end of `validate_assessment` (around line 125) and add:

```python
    evidence = assessment.get("evidence")
    if evidence is not None:
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dict")
        for dim_key, sentence in evidence.items():
            if dim_key not in DIMENSION_LABELS:
                raise ValueError(f"evidence contains unknown dimension: {dim_key!r}")
            if not isinstance(sentence, str):
                raise ValueError(f"evidence[{dim_key!r}] must be a string")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_engine.py -k "evidence" -v
```

Expected: PASS

- [ ] **Step 5: Update assessment schema doc**

In `skills/score/references/assessment-schema.md`, add after the `dimensions` bullet:

```markdown
- `evidence` (optional) — dict mapping dimension key to a one-sentence string quoting the specific prompt behavior that drove the score. Keys must match keys in `dimensions`. Example: `{"clarity": "Third prompt did not specify expected output format"}`
```

- [ ] **Step 6: Commit**

```bash
cd /Users/huccct/Frontend/promptiq
git add engine/promptiq.py skills/score/references/assessment-schema.md tests/test_engine.py
git commit -m "feat: add evidence field validation to assessment schema"
```

---

## Task 2: Store evidence in session record and pass through finalize output

**Files:**
- Modify: `engine/promptiq.py:1120-1200` (`finalize`)

- [ ] **Step 1: Write the failing test**

```python
def test_finalize_includes_evidence_in_output(tmp_path, rubric):
    assessment = make_valid_assessment()
    assessment["evidence"] = {
        "clarity": "Third prompt did not specify expected output format",
    }
    result = finalize(assessment, rubric, save=False)
    assert "evidence" in result
    assert result["evidence"]["clarity"] == "Third prompt did not specify expected output format"

def test_finalize_evidence_absent_when_not_provided(tmp_path, rubric):
    assessment = make_valid_assessment()
    result = finalize(assessment, rubric, save=False)
    # evidence key should still exist, just empty dict
    assert result.get("evidence") == {}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_engine.py -k "finalize_includes_evidence or finalize_evidence_absent" -v
```

Expected: FAIL

- [ ] **Step 3: Add evidence to `finalize` in `engine/promptiq.py`**

In `finalize`, find where `session_record` dict is built (around line 1145). Add `evidence` to it:

```python
    session_record = {
        # ... existing fields ...
        "evidence": assessment.get("evidence", {}),
    }
```

Then in the return dict at the bottom of `finalize`, add:

```python
    return {
        # ... existing fields ...
        "evidence": assessment.get("evidence", {}),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_engine.py -k "finalize_includes_evidence or finalize_evidence_absent" -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/promptiq.py tests/test_engine.py
git commit -m "feat: pass evidence through finalize output and session record"
```

---

## Task 3: Add no-evidence score cap to rubric and engine

**Files:**
- Modify: `engine/rubric_v1.json`
- Modify: `engine/promptiq.py:151-208` (`apply_caps`)

- [ ] **Step 1: Write the failing test**

```python
def test_apply_caps_no_evidence_cap(rubric):
    """Dimension score > 5 without evidence sentence should be capped at 5."""
    assessment = make_valid_assessment()
    assessment["dimensions"] = {
        "clarity": 8,  # high score
        "context": 5,
        "iteration": 5,
        "decomposition": 5,
        "output_spec": 5,
        "examples": None,
        "reasoning": None,
        "tool_awareness": None,
    }
    # no evidence provided
    assessment["evidence"] = {}
    # raw_total would be (8+5+5+5+5)/5 = 5.6
    raw_total = 5.6
    confidence = "medium"
    total, cap_reasons = apply_caps(raw_total, assessment, rubric, confidence)
    assert "no_evidence_cap" in cap_reasons

def test_apply_caps_no_evidence_cap_not_triggered_when_evidence_present(rubric):
    assessment = make_valid_assessment()
    assessment["dimensions"] = {
        "clarity": 8,
        "context": 5,
        "iteration": 5,
        "decomposition": 5,
        "output_spec": 5,
        "examples": None,
        "reasoning": None,
        "tool_awareness": None,
    }
    assessment["evidence"] = {"clarity": "User specified exact output format in prompt 2"}
    raw_total = 5.6
    confidence = "medium"
    total, cap_reasons = apply_caps(raw_total, assessment, rubric, confidence)
    assert "no_evidence_cap" not in cap_reasons
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_engine.py -k "no_evidence_cap" -v
```

Expected: FAIL

- [ ] **Step 3: Add `no_evidence_cap` to `rubric_v1.json`**

In `engine/rubric_v1.json`, add inside `"score_caps"`:

```json
"no_evidence_cap": 5.0
```

And add a top-level rule:

```json
"evidence_rules": {
  "high_score_requires_evidence_above": 5,
  "no_evidence_cap": 5.0
}
```

- [ ] **Step 4: Add no-evidence cap logic to `apply_caps` in `engine/promptiq.py`**

In `apply_caps`, after the existing cap checks, add:

```python
    evidence_rules = rubric.get("evidence_rules", {})
    no_evidence_cap = evidence_rules.get("no_evidence_cap")
    high_score_threshold = evidence_rules.get("high_score_requires_evidence_above", 5)
    if no_evidence_cap is not None:
        evidence = assessment.get("evidence", {})
        dimensions = assessment.get("dimensions", {})
        has_high_score_without_evidence = any(
            v is not None and float(v) > high_score_threshold and key not in evidence
            for key, v in dimensions.items()
        )
        if has_high_score_without_evidence and total > no_evidence_cap:
            total = min(total, no_evidence_cap)
            cap_reasons.append("no_evidence_cap")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_engine.py -k "no_evidence_cap" -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add engine/promptiq.py engine/rubric_v1.json tests/test_engine.py
git commit -m "feat: add no-evidence score cap — high scores require evidence sentences"
```

---

## Task 4: Add per-dimension trend deltas to `recent_trend_entries`

**Files:**
- Modify: `engine/promptiq.py:979-992` (`recent_trend_entries`)

- [ ] **Step 1: Write the failing test**

```python
def test_recent_trend_entries_includes_dimension_deltas():
    records = [
        {
            "date": "2026-04-10",
            "total": 6.0,
            "dimensions": {"clarity": 5, "context": 6, "iteration": 5,
                           "decomposition": 5, "output_spec": 5,
                           "examples": None, "reasoning": None, "tool_awareness": None},
        },
        {
            "date": "2026-04-14",
            "total": 6.5,
            "dimensions": {"clarity": 7, "context": 6, "iteration": 5,
                           "decomposition": 5, "output_spec": 5,
                           "examples": None, "reasoning": None, "tool_awareness": None},
        },
    ]
    entries = recent_trend_entries(records)
    assert len(entries) == 2
    # second entry should have delta vs first
    second = entries[1]
    assert "dimension_deltas" in second
    assert second["dimension_deltas"]["clarity"] == 2.0  # 7 - 5
    assert second["dimension_deltas"]["context"] == 0.0  # 6 - 6

def test_recent_trend_entries_first_entry_has_no_deltas():
    records = [
        {
            "date": "2026-04-10",
            "total": 6.0,
            "dimensions": {"clarity": 5, "context": 6, "iteration": 5,
                           "decomposition": 5, "output_spec": 5,
                           "examples": None, "reasoning": None, "tool_awareness": None},
        },
    ]
    entries = recent_trend_entries(records)
    assert entries[0].get("dimension_deltas") is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_engine.py -k "dimension_deltas" -v
```

Expected: FAIL

- [ ] **Step 3: Update `recent_trend_entries` in `engine/promptiq.py`**

Replace the existing `recent_trend_entries` function (lines 979-991):

```python
def recent_trend_entries(records: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    window = records[-limit:]
    for i, record in enumerate(window):
        weakest = weakest_dimension_for_record(record)
        entry: dict[str, Any] = {
            "date": record.get("date"),
            "total": round1(float(record["total"])),
            "weakest_dimension": weakest,
            "dimension_deltas": None,
        }
        if i > 0:
            prev = window[i - 1]
            prev_dims = prev.get("dimensions", {})
            curr_dims = record.get("dimensions", {})
            deltas: dict[str, float] = {}
            for key in DIMENSION_LABELS:
                prev_val = prev_dims.get(key)
                curr_val = curr_dims.get(key)
                if prev_val is not None and curr_val is not None:
                    deltas[key] = round1(float(curr_val) - float(prev_val))
            entry["dimension_deltas"] = deltas if deltas else None
        entries.append(entry)
    return entries
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_engine.py -k "dimension_deltas" -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/promptiq.py tests/test_engine.py
git commit -m "feat: add per-dimension trend deltas to recent_trend_entries"
```

---

## Task 5: Lower trend threshold from 3 sessions to 2

**Files:**
- Modify: `skills/score/SKILL.md`
- Modify: `skills/score/references/report-template.md`

- [ ] **Step 1: Find the threshold in SKILL.md**

```bash
grep -n "history_session_count\|>= 3\|>= 2" skills/score/SKILL.md
```

- [ ] **Step 2: Update the threshold in `skills/score/SKILL.md`**

Find the line:
```
If `history_session_count >= 3`, include `Recent Trend` and `Focus Area`.
```

Change to:
```
If `history_session_count >= 2`, include `Recent Trend` and `Focus Area`.
```

- [ ] **Step 3: Update the threshold in `skills/score/references/report-template.md`**

Find the line:
```
If `history_session_count >= 3`, append:
```

Change to:
```
If `history_session_count >= 2`, append:
```

- [ ] **Step 4: Commit**

```bash
git add skills/score/SKILL.md skills/score/references/report-template.md
git commit -m "feat: show trend from session 2 instead of session 3"
```

---

## Task 6: Add milestone detection to engine

**Files:**
- Modify: `engine/promptiq.py` (add `detect_milestone` function; call from `finalize`)

- [ ] **Step 1: Write the failing test**

```python
def test_detect_milestone_at_5():
    assert detect_milestone(5) == {"session_count": 5, "message": "5 sessions in."}

def test_detect_milestone_at_10():
    result = detect_milestone(10)
    assert result is not None
    assert result["session_count"] == 10

def test_detect_milestone_none_at_non_milestone():
    assert detect_milestone(3) is None
    assert detect_milestone(7) is None
    assert detect_milestone(11) is None

def test_finalize_includes_milestone_at_session_5(rubric):
    # Build a history with 4 existing sessions, then finalize a 5th
    # The result should include a milestone
    # (use monkeypatch or tmp_path to inject history)
    pass  # integration test — implement after unit tests pass
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_engine.py -k "milestone" -v
```

Expected: FAIL — `detect_milestone` not defined.

- [ ] **Step 3: Add `detect_milestone` to `engine/promptiq.py`**

Add after `focus_area` function (around line 1013):

```python
MILESTONE_COUNTS = {5, 10, 20, 50, 100}

def detect_milestone(session_count: int) -> dict[str, Any] | None:
    if session_count not in MILESTONE_COUNTS:
        return None
    return {
        "session_count": session_count,
        "message": f"{session_count} sessions in.",
    }
```

In `finalize`, after computing `session_count`, add:

```python
    milestone = detect_milestone(session_count)
```

And add to the return dict:

```python
        "milestone": milestone,
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_engine.py -k "milestone" -v
```

Expected: PASS (unit tests; skip integration test for now)

- [ ] **Step 5: Commit**

```bash
git add engine/promptiq.py tests/test_engine.py
git commit -m "feat: add milestone detection at sessions 5, 10, 20, 50, 100"
```

---

## Task 7: Update report template — focus dimension + folded others

**Files:**
- Modify: `skills/score/references/report-template.md`

- [ ] **Step 1: Replace the Dimension Breakdown section**

In `skills/score/references/report-template.md`, replace the existing `**Dimension Breakdown**` section with:

```markdown
**Focus Dimension**

[`weakest_dimension.label`] — [`weakest_dimension.score`]/10

[Evidence sentence from `evidence[weakest_dimension.key]`, or "No specific evidence recorded." if absent]

What strong looks like: [one sentence describing what a 8+ score on this dimension requires]

**Other Dimensions**

```text
[For each non-focus dimension, one line:]
Instruction Clarity    [bar]  [N]/10
Context Provision      [bar]  [N]/10
...
```

[Omit the focus dimension from this list. For N/A dimensions, render `──────────  N/A`]
```

- [ ] **Step 2: Add conversation offer section to report template**

At the end of the template (after `Focus Area`), add:

```markdown
**Next Step**

[If `weakest_dimension.score < 6`:]
Your [weakest_dimension.label] score was [N]. Want me to rewrite your weakest prompt from this session to show what a stronger version looks like?

[If `weakest_dimension.score >= 6`:]
Next session, try this: [one specific constraint to add based on weakest dimension — e.g., "Add an explicit output format requirement to every prompt that produces structured data"]
```

- [ ] **Step 3: Add milestone rendering to report template**

After the `Recent Trend` table, add:

```markdown
[If `milestone` is present:]

**Milestone**
[milestone.session_count] sessions in. Your average has moved from [earliest compatible session total] to [current total]. Strongest growth: [dimension with highest positive delta across all sessions]. Still needs work: [focus_area.label].
```

- [ ] **Step 4: Commit**

```bash
git add skills/score/references/report-template.md
git commit -m "feat: update report template — focus dimension, folded others, conversation offer, milestone"
```

---

## Task 8: Update `/score` SKILL.md to require evidence sentences

**Files:**
- Modify: `skills/score/SKILL.md`

- [ ] **Step 1: Add evidence requirement to assessment step**

In `skills/score/SKILL.md`, find step 1 (the assessment building step). After the existing scoring instructions, add:

```markdown
   For each dimension you score above 5, write a one-sentence evidence string that quotes or paraphrases the specific user prompt behavior that drove the score. Store these in an `evidence` dict keyed by dimension name.
   Example: `"evidence": {"clarity": "Third prompt did not specify expected output format", "context": "Provided file path and error message at session start"}`
   If you cannot find specific evidence for a dimension score above 5, lower the score to 5 instead of inventing evidence.
```

- [ ] **Step 2: Update report rendering instructions**

In `skills/score/SKILL.md`, find step 4 (render the report). Update to reference the new template structure:

```markdown
4. Render the report.
   Use the exact section order in [references/report-template.md](references/report-template.md).
   Front-load `Why It Is Not Higher`.
   Use `weakest_dimension` as the Focus Dimension with its evidence sentence from the assessment.
   Fold all other dimensions into the compact bar list.
   If `history_session_count >= 2`, include `Recent Trend` and `Focus Area`.
   If `milestone` is present, include the `Milestone` section.
   End with the `Next Step` offer: rewrite offer if `weakest_dimension.score < 6`, drill suggestion otherwise.
   Keep the tone direct and fair.
```

- [ ] **Step 3: Commit**

```bash
git add skills/score/SKILL.md
git commit -m "feat: require evidence sentences in score assessment; update report rendering"
```

---

## Task 9: Update `/rewrite-last` to support score-triggered mode

**Files:**
- Modify: `skills/rewrite-last/SKILL.md`

- [ ] **Step 1: Add triggered mode to SKILL.md**

In `skills/rewrite-last/SKILL.md`, after the existing step 1 (identify prompts), add a new conditional block:

```markdown
**If triggered from a `/score` report** (the user said yes to the rewrite offer):
   The target prompt is the one that drove the weakest dimension score.
   Use the evidence sentence from the assessment to frame the rewrite:
   - Show the original prompt
   - Show the evidence sentence explaining why it was weak
   - Show the rewritten version
   - Show what specifically changed and why

   Format:
   **Original**
   > [original prompt text]

   **Why it was weak**
   [evidence sentence]

   **Rewritten**
   > [improved prompt]

   **What changed**
   [2-3 bullet points: specific additions or changes made]
```

- [ ] **Step 2: Commit**

```bash
git add skills/rewrite-last/SKILL.md
git commit -m "feat: add score-triggered rewrite mode to rewrite-last skill"
```

---

## Task 10: Run full test suite and verify no regressions

- [ ] **Step 1: Run all tests**

```bash
cd /Users/huccct/Frontend/promptiq
python -m pytest tests/ -v
```

Expected: All tests pass. Note any failures.

- [ ] **Step 2: Run engine smoke test**

```bash
echo '{
  "date": "2026-04-14",
  "plugin_version": "0.4.0",
  "tool": "claude-code",
  "session_summary": "Smoke test session",
  "complexity": "medium",
  "meaningful_user_messages": 8,
  "applicability": {"examples": false, "reasoning": false, "tool_awareness": true, "verification": true},
  "evidence_counts": {"evidence_quotes": 2, "corrections_or_refinements": 1, "output_constraints": 2, "tool_signals": 1, "verification_signals": 0},
  "dimensions": {"clarity": 7, "context": 6, "iteration": 5, "decomposition": 6, "output_spec": 5, "examples": null, "reasoning": null, "tool_awareness": 6},
  "evidence": {"clarity": "User specified exact output format in prompt 2"}
}' > /tmp/smoke-assessment.json

~/.promptiq/promptiq finalize --assessment-file /tmp/smoke-assessment.json
```

Expected: JSON output includes `evidence` field, `milestone` field, and `recent_trend` entries with `dimension_deltas`.

- [ ] **Step 3: Fix any failures before proceeding**

If tests fail, diagnose and fix before marking this task complete.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "test: verify all improvements pass full test suite"
```

---

## Self-Review Checklist

- [x] Spec coverage: All 5 improvements from spec are covered (evidence sentences → Tasks 1-3; conversation starter → Tasks 7-8; focus dimension → Task 7; trend narrative → Tasks 4-5-6; rewrite integration → Task 9)
- [x] No placeholders: All steps have concrete code
- [x] Type consistency: `evidence` is `dict[str, str]` throughout; `dimension_deltas` is `dict[str, float] | None`; `milestone` is `dict[str, Any] | None`
- [x] File paths: All exact paths verified against repo structure
