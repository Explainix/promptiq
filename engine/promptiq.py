#!/usr/bin/env python3
"""PromptIQ local helper.

This helper keeps deterministic logic out of the prompt:
- total calculation
- N/A filtering
- score caps
- confidence determination
- versioned history persistence
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

DIMENSION_LABELS = {
    "clarity": "Instruction Clarity",
    "context": "Context Provision",
    "iteration": "Iteration Quality",
    "decomposition": "Task Decomposition",
    "output_spec": "Output Specification",
    "examples": "Example Usage",
    "reasoning": "Reasoning Elicitation",
    "tool_awareness": "Tool Awareness",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def load_assessment_payload(raw_json: str | None, raw_file: str | None) -> dict[str, Any]:
    if raw_json is None and raw_file is None:
        raise ValueError("either --assessment-json or --assessment-file is required")
    if raw_json is not None and raw_file is not None:
        raise ValueError("use only one of --assessment-json or --assessment-file")
    if raw_file is not None:
        return load_json(Path(raw_file))
    return json.loads(raw_json)


def round1(value: float) -> float:
    return round(value + 1e-9, 1)


def compute_average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def validate_assessment(assessment: dict[str, Any]) -> None:
    required_keys = [
        "date",
        "plugin_version",
        "tool",
        "session_summary",
        "complexity",
        "meaningful_user_messages",
        "applicability",
        "evidence_counts",
        "dimensions",
    ]
    missing = [key for key in required_keys if key not in assessment]
    if missing:
        raise ValueError(f"assessment missing required keys: {', '.join(missing)}")

    if assessment["complexity"] not in {"low", "medium", "high"}:
        raise ValueError("complexity must be one of: low, medium, high")

    applicability = assessment["applicability"]
    required_applicability = ["examples", "reasoning", "tool_awareness"]
    missing_applicability = [key for key in required_applicability if key not in applicability]
    if missing_applicability:
        raise ValueError(f"applicability missing keys: {', '.join(missing_applicability)}")

    dimensions = assessment["dimensions"]
    unknown_dimensions = [key for key in dimensions if key not in DIMENSION_LABELS]
    if unknown_dimensions:
        raise ValueError(f"unknown dimensions: {', '.join(sorted(unknown_dimensions))}")

    for key, value in dimensions.items():
        if value is None:
            continue
        numeric = float(value)
        if numeric < 1 or numeric > 10:
            raise ValueError(f"{key} must be between 1 and 10")


def derive_confidence(assessment: dict[str, Any], rubric: dict[str, Any]) -> str:
    rules = rubric["confidence_rules"]
    message_count = int(assessment.get("meaningful_user_messages", 0))
    complexity = assessment.get("complexity", "low")
    evidence_quotes = int(assessment.get("evidence_counts", {}).get("evidence_quotes", 0))

    if message_count < rules["low_if_meaningful_user_messages_below"]:
        return "low"
    if complexity in rules["low_if_complexity_is"]:
        return "low"

    high_requires = rules["high_requires"]
    if (
        message_count >= high_requires["meaningful_user_messages_at_least"]
        and complexity in high_requires["complexity_in"]
        and evidence_quotes >= high_requires["evidence_quotes_at_least"]
    ):
        return "high"

    if message_count < rules["medium_if_meaningful_user_messages_below"]:
        return "medium"

    return "medium"


def apply_caps(raw_total: float, assessment: dict[str, Any], rubric: dict[str, Any], confidence: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    capped = raw_total
    caps = rubric["score_caps"]

    message_count = int(assessment.get("meaningful_user_messages", 0))
    complexity = assessment.get("complexity", "low")
    evidence = assessment.get("evidence_counts", {})

    if message_count < rubric["confidence_rules"]["low_if_meaningful_user_messages_below"] and capped > caps["short_session_cap"]:
        capped = caps["short_session_cap"]
        reasons.append("short_session_cap")

    if complexity == "low" and capped > caps["low_complexity_cap"]:
        capped = caps["low_complexity_cap"]
        reasons.append("low_complexity_cap")

    if confidence == "low" and capped > caps["low_confidence_cap"]:
        capped = caps["low_confidence_cap"]
        reasons.append("low_confidence_cap")

    gates = rubric["high_score_gates"]

    if capped > 7.5:
        gate = gates["above_7_5"]
        if (
            int(evidence.get("evidence_quotes", 0)) < gate["min_evidence_quotes"]
            or int(evidence.get("corrections_or_refinements", 0)) < gate["min_corrections_or_refinements"]
            or int(evidence.get("output_constraints", 0)) < gate["min_output_constraints"]
        ):
            capped = min(capped, 7.4)
            reasons.append("above_7_5_gate_failed")

    if capped > 8.5:
        gate = gates["above_8_5"]
        if (
            assessment.get("complexity") != gate["complexity_must_be"]
            or confidence == gate["confidence_cannot_be"]
            or int(evidence.get("evidence_quotes", 0)) < gate["min_evidence_quotes"]
            or int(evidence.get("corrections_or_refinements", 0)) < gate["min_corrections_or_refinements"]
            or int(evidence.get("output_constraints", 0)) < gate["min_output_constraints"]
            or int(evidence.get("tool_signals", 0)) < gate["min_tool_signals"]
        ):
            capped = min(capped, 8.4)
            reasons.append("above_8_5_gate_failed")

    return round1(capped), reasons


def history_path(rubric: dict[str, Any]) -> Path:
    raw = rubric["history"]["path"]
    return Path(os.path.expanduser(raw))


def load_history(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"sessions": []}
    try:
        with path.open() as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {
            "sessions": [],
            "_warning": "history_corrupted",
        }


def save_history(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def compatible_sessions(history: dict[str, Any], rubric_version: str) -> list[dict[str, Any]]:
    return [s for s in history.get("sessions", []) if s.get("rubric_version") == rubric_version]


def weakest_dimension(dimensions: dict[str, Any]) -> dict[str, Any] | None:
    scored = [(key, float(value)) for key, value in dimensions.items() if value is not None]
    if not scored:
        return None
    key, score = min(scored, key=lambda item: item[1])
    return {
        "key": key,
        "label": DIMENSION_LABELS[key],
        "score": round1(score),
    }


def weakest_dimension_for_record(record: dict[str, Any]) -> dict[str, Any] | None:
    stored = record.get("weakest_dimension")
    if stored:
        return stored
    return weakest_dimension(record.get("dimensions", {}))


def score_band(total: float, rubric: dict[str, Any]) -> str:
    bands = sorted(rubric.get("score_bands", []), key=lambda band: band["min_total"])
    current = bands[0]["label"] if bands else "unrated"
    for band in bands:
        if total >= float(band["min_total"]):
            current = band["label"]
    return current


def next_band(total: float, rubric: dict[str, Any]) -> dict[str, Any] | None:
    bands = sorted(rubric.get("score_bands", []), key=lambda band: band["min_total"])
    for band in bands:
        if total < float(band["min_total"]):
            return {
                "label": band["label"],
                "target_total": round1(float(band["min_total"])),
            }
    return None


def next_band_requirements(target_total: float, confidence: str, assessment: dict[str, Any], cap_reasons: list[str]) -> list[str]:
    evidence = assessment.get("evidence_counts", {})
    requirements: list[str] = []

    if cap_reasons:
        if "short_session_cap" in cap_reasons:
            requirements.append("The session is too short to justify a higher score. More meaningful turns are required.")
        if "low_complexity_cap" in cap_reasons:
            requirements.append("The task complexity is too low. Easy asks cannot score like hard collaborative work.")
        if "low_confidence_cap" in cap_reasons:
            requirements.append("Evidence coverage is too thin. The model does not have enough signal to trust a higher total.")

    if target_total >= 6.5:
        if int(assessment.get("meaningful_user_messages", 0)) < 4:
            requirements.append("Reach at least 4 meaningful user turns before aiming above the beginner band.")
        if int(evidence.get("output_constraints", 0)) < 1:
            requirements.append("State at least one concrete output constraint instead of leaving format and depth implicit.")

    if target_total >= 7.5:
        if int(evidence.get("evidence_quotes", 0)) < 2:
            requirements.append("Provide enough concrete steering that the review can cite at least 2 strong evidence moments.")
        if int(evidence.get("corrections_or_refinements", 0)) < 1:
            requirements.append("Refine or correct the AI at least once instead of accepting the first pass.")
        if int(evidence.get("output_constraints", 0)) < 1:
            requirements.append("Set explicit success criteria or output format before pushing for a strong score.")

    if target_total >= 8.5:
        if assessment.get("complexity") != "high":
            requirements.append("Scores in the elite band require a genuinely high-complexity session.")
        if confidence == "low":
            requirements.append("Low-confidence sessions cannot enter the elite band.")
        if int(evidence.get("evidence_quotes", 0)) < 3:
            requirements.append("Elite scores require at least 3 distinct evidence moments, not one or two isolated good prompts.")
        if int(evidence.get("corrections_or_refinements", 0)) < 2:
            requirements.append("Elite scores require multiple steering corrections, not a single refinement.")
        if int(evidence.get("output_constraints", 0)) < 2:
            requirements.append("Elite scores require repeated output control across the session.")
        if int(evidence.get("tool_signals", 0)) < 1:
            requirements.append("Use at least one relevant tool or AI-native workflow feature when the task benefits from it.")

    if not requirements:
        requirements.append("The next band needs cleaner evidence than this session provided.")

    return requirements


def recent_trend_entries(records: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in records[-limit:]:
        weakest = weakest_dimension_for_record(record)
        entries.append(
            {
                "date": record.get("date"),
                "total": round1(float(record["total"])),
                "weakest_dimension": weakest,
            }
        )
    return entries


def focus_area(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    scores_by_dimension: dict[str, list[float]] = {}

    for record in records:
        for key, value in record.get("dimensions", {}).items():
            if key not in DIMENSION_LABELS or value is None:
                continue
            scores_by_dimension.setdefault(key, []).append(float(value))

    if not scores_by_dimension:
        return None

    lowest_key = min(scores_by_dimension, key=lambda key: compute_average(scores_by_dimension[key]))
    average_score = round1(compute_average(scores_by_dimension[lowest_key]))
    return {
        "key": lowest_key,
        "label": DIMENSION_LABELS[lowest_key],
        "average_score": average_score,
    }


def compute_trend(history: dict[str, Any], rubric_version: str, total: float) -> dict[str, Any] | None:
    sessions = compatible_sessions(history, rubric_version)
    if not sessions:
        return None
    last = sessions[-1]
    last_total = float(last["total"])
    return {
        "last_total": round1(last_total),
        "delta": round1(total - last_total),
        "session_count": len(sessions) + 1
    }


def finalize(assessment: dict[str, Any], rubric: dict[str, Any], save: bool) -> dict[str, Any]:
    validate_assessment(assessment)
    dimensions = assessment["dimensions"]
    scored_values = [float(v) for v in dimensions.values() if v is not None]
    raw_total = round1(compute_average(scored_values))
    confidence = derive_confidence(assessment, rubric)
    total, cap_reasons = apply_caps(raw_total, assessment, rubric, confidence)
    band = score_band(total, rubric)
    weakest = weakest_dimension(dimensions)
    next_target = next_band(total, rubric)
    why_not_higher = []
    if next_target is not None:
        why_not_higher = next_band_requirements(
            next_target["target_total"],
            confidence,
            assessment,
            cap_reasons,
        )

    hist_path = history_path(rubric)
    history = load_history(hist_path)
    history_warning = history.get("_warning")
    trend = compute_trend(history, rubric["rubric_version"], total)

    session_record = {
        "date": assessment["date"],
        "total": total,
        "raw_total": raw_total,
        "complexity": assessment.get("complexity"),
        "confidence": confidence,
        "rubric_version": rubric["rubric_version"],
        "plugin_version": assessment.get("plugin_version"),
        "tool": assessment.get("tool"),
        "meaningful_user_messages": assessment.get("meaningful_user_messages"),
        "evidence_counts": assessment.get("evidence_counts", {}),
        "cap_reasons": cap_reasons,
        "score_band": band,
        "weakest_dimension": weakest,
        "dimensions": dimensions,
        "applicability": assessment.get("applicability", {}),
        "session_summary": assessment.get("session_summary", ""),
    }

    analytics_records = compatible_sessions(history, rubric["rubric_version"]) + [session_record]
    session_count = len(analytics_records)
    recent_trend = recent_trend_entries(analytics_records)
    weakest_focus_area = focus_area(analytics_records)

    if save:
        history.setdefault("sessions", []).append(session_record)
        save_history(hist_path, history)

    return {
        "total": total,
        "raw_total": raw_total,
        "confidence": confidence,
        "cap_reasons": cap_reasons,
        "score_band": band,
        "weakest_dimension": weakest,
        "next_band": next_target,
        "why_not_higher": why_not_higher,
        "recent_trend": recent_trend,
        "focus_area": weakest_focus_area,
        "history_session_count": session_count,
        "history_warning": history_warning,
        "trend": trend,
        "session_record": session_record,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["finalize"])
    parser.add_argument("--assessment-json")
    parser.add_argument("--assessment-file")
    parser.add_argument("--rubric", default=str(Path(__file__).with_name("rubric_v1.json")))
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    assessment = load_assessment_payload(args.assessment_json, args.assessment_file)
    rubric = load_json(Path(args.rubric))

    if args.command == "finalize":
        result = finalize(assessment, rubric, args.save)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
