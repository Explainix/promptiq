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
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
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

DEFAULT_PROMPTIQ_HOME = "~/.promptiq"
DEFAULT_HISTORY_PATH = f"{DEFAULT_PROMPTIQ_HOME}/history.json"
DEFAULT_IMPORTS_DIR = f"{DEFAULT_PROMPTIQ_HOME}/imports"
DEFAULT_BIN_DIR = "~/.local/bin"
DEFAULT_RUBRIC_FILENAME = "rubric_v1.json"
ROLE_ALIASES = {
    "ai": "assistant",
    "human": "user",
    "model": "assistant",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_assessment_payload(raw_json: str | None, raw_file: str | None) -> dict[str, Any]:
    if raw_json is None and raw_file is None:
        raise ValueError("either --assessment-json or --assessment-file is required")
    if raw_json is not None and raw_file is not None:
        raise ValueError("use only one of --assessment-json or --assessment-file")
    if raw_file is not None:
        return load_json(Path(raw_file))
    return json.loads(raw_json)


def load_session_payload(raw_json: str | None, raw_file: str | None) -> Any:
    if raw_json is None and raw_file is None:
        raise ValueError("either --session-json or --session-file is required")
    if raw_json is not None and raw_file is not None:
        raise ValueError("use only one of --session-json or --session-file")
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

    for optional_key in ["session_id", "session_fingerprint", "model_version"]:
        if optional_key in assessment and assessment[optional_key] is not None and not isinstance(assessment[optional_key], str):
            raise ValueError(f"{optional_key} must be a string when provided")

    applicability = assessment["applicability"]
    required_applicability = ["examples", "reasoning", "tool_awareness", "verification"]
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

    evidence = assessment.get("evidence")
    if evidence is not None:
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be a dict")
        for dim_key, sentence in evidence.items():
            if dim_key not in DIMENSION_LABELS:
                raise ValueError(f"evidence contains unknown dimension: {dim_key!r}")
            if not isinstance(sentence, str):
                raise ValueError(f"evidence[{dim_key!r}] must be a string")


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
    applicability = assessment.get("applicability", {})

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
            or (
                applicability.get("verification")
                and int(evidence.get("verification_signals", 0)) < gate.get("min_verification_signals_if_applicable", 0)
            )
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
            or (
                applicability.get("verification")
                and int(evidence.get("verification_signals", 0)) < gate.get("min_verification_signals_if_applicable", 0)
            )
        ):
            capped = min(capped, 8.4)
            reasons.append("above_8_5_gate_failed")

    evidence_rules = rubric.get("evidence_rules", {})
    no_evidence_cap = evidence_rules.get("no_evidence_cap")
    high_score_threshold = evidence_rules.get("high_score_requires_evidence_above", 5)
    if no_evidence_cap is not None and "evidence" in assessment:
        evidence_field = assessment.get("evidence", {})
        dimensions = assessment.get("dimensions", {})
        has_high_score_without_evidence = any(
            v is not None and float(v) > high_score_threshold and key not in evidence_field
            for key, v in dimensions.items()
        )
        if has_high_score_without_evidence and capped > no_evidence_cap:
            capped = min(capped, no_evidence_cap)
            reasons.append("no_evidence_cap")

    return round1(capped), reasons


def resolve_promptiq_home() -> Path:
    return Path(os.path.expanduser(os.environ.get("PROMPTIQ_HOME", DEFAULT_PROMPTIQ_HOME)))


def resolved_history_path(raw: str = DEFAULT_HISTORY_PATH) -> Path:
    override = os.environ.get("PROMPTIQ_HISTORY_PATH")
    if override:
        return Path(os.path.expanduser(override))

    promptiq_home = os.environ.get("PROMPTIQ_HOME")
    if promptiq_home and raw == DEFAULT_HISTORY_PATH:
        return Path(os.path.expanduser(promptiq_home)) / "history.json"
    return Path(os.path.expanduser(raw))


def history_path(rubric: dict[str, Any]) -> Path:
    return resolved_history_path(rubric["history"]["path"])


def resolved_launcher_path() -> Path:
    return resolve_promptiq_home() / "promptiq"


def resolved_bin_dir(raw: str = DEFAULT_BIN_DIR) -> Path:
    override = os.environ.get("PROMPTIQ_BIN_DIR")
    if override:
        return Path(os.path.expanduser(override))
    return Path(os.path.expanduser(raw))


def resolved_bin_launcher_path() -> Path:
    return resolved_bin_dir() / "promptiq"


def resolved_imports_dir(raw: str = DEFAULT_IMPORTS_DIR) -> Path:
    override = os.environ.get("PROMPTIQ_IMPORTS_PATH")
    if override:
        return Path(os.path.expanduser(override))

    promptiq_home = os.environ.get("PROMPTIQ_HOME")
    if promptiq_home and raw == DEFAULT_IMPORTS_DIR:
        return Path(os.path.expanduser(promptiq_home)) / "imports"
    return Path(os.path.expanduser(raw))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def iso_date() -> str:
    return datetime.now().date().isoformat()


def fingerprint_digest(fingerprint: str) -> str:
    return fingerprint.split(":", 1)[-1][:12]


def slugify_identifier(value: str) -> str:
    candidate = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    if not candidate:
        candidate = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    if candidate != value:
        candidate = f"{candidate}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:8]}"
    return candidate


def extract_text_fragments(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []

    if isinstance(value, list):
        fragments: list[str] = []
        for item in value:
            fragments.extend(extract_text_fragments(item))
        return fragments

    if isinstance(value, dict):
        for key in ("text", "value"):
            text = value.get(key)
            if isinstance(text, str) and text.strip():
                return [text.strip()]

        nested = value.get("content")
        if nested is not None:
            return extract_text_fragments(nested)

    return []


def normalize_message_content(value: Any) -> str:
    fragments = extract_text_fragments(value)
    text = "\n".join(fragment for fragment in fragments if fragment)
    if not text.strip():
        raise ValueError("message content must include text")
    return text.strip()


def normalize_message_role(role: Any) -> str:
    if not isinstance(role, str) or not role.strip():
        raise ValueError("message role must be a non-empty string")
    normalized = role.strip().lower()
    return ROLE_ALIASES.get(normalized, normalized)


def normalize_transcript_message(message: Any) -> dict[str, str]:
    if not isinstance(message, dict):
        raise ValueError("each transcript message must be an object")

    content = message.get("content")
    if content is None and "parts" in message:
        content = message["parts"]
    if content is None and "text" in message:
        content = message["text"]
    if content is None:
        raise ValueError("each transcript message must include content")

    return {
        "role": normalize_message_role(message.get("role")),
        "content": normalize_message_content(content),
    }


def extract_transcript_messages(payload: Any) -> tuple[list[Any], dict[str, Any]]:
    if isinstance(payload, list):
        return payload, {}

    if not isinstance(payload, dict):
        raise ValueError("session payload must be an object or a raw message array")

    if "transcript" in payload:
        transcript = payload["transcript"]
        if not isinstance(transcript, list):
            raise ValueError("session payload field 'transcript' must be an array")
        return transcript, payload

    if "messages" in payload:
        messages = payload["messages"]
        if not isinstance(messages, list):
            raise ValueError("session payload field 'messages' must be an array")
        return messages, payload

    raise ValueError("session payload must include 'transcript' or 'messages', or be a raw message array")


def derive_import_session_fingerprint(messages: list[dict[str, str]], tool: str, model_version: str | None) -> str:
    digest = hashlib.sha256(
        canonical_json(
            {
                "tool": tool,
                "model_version": model_version,
                "messages": messages,
            }
        ).encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest}"


def normalize_transcript_bundle(payload: Any, source_path: Path | None = None) -> dict[str, Any]:
    raw_messages, metadata = extract_transcript_messages(payload)
    messages = [normalize_transcript_message(message) for message in raw_messages]
    if not messages:
        raise ValueError("session payload must contain at least one message")

    tool = metadata.get("tool")
    if not isinstance(tool, str) or not tool.strip():
        tool = "imported"
    else:
        tool = tool.strip()

    model_version = metadata.get("model_version")
    if not isinstance(model_version, str) or not model_version.strip():
        model_version = None
    else:
        model_version = model_version.strip()

    explicit_fingerprint = metadata.get("session_fingerprint")
    if not isinstance(explicit_fingerprint, str) or not explicit_fingerprint.strip():
        explicit_fingerprint = None

    session_fingerprint = explicit_fingerprint or derive_import_session_fingerprint(messages, tool, model_version)
    session_id = metadata.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        session_id = f"import-{fingerprint_digest(session_fingerprint)}"
    else:
        session_id = session_id.strip()

    session_summary = metadata.get("session_summary") or metadata.get("description") or metadata.get("name")
    if not isinstance(session_summary, str) or not session_summary.strip():
        session_summary = None
    else:
        session_summary = session_summary.strip()

    bundle = {
        "session_id": session_id,
        "session_fingerprint": session_fingerprint,
        "tool": tool,
        "model_version": model_version,
        "source_path": str(source_path.resolve()) if source_path is not None else None,
        "imported_at": iso_timestamp(),
        "message_count": len(messages),
        "user_message_count": sum(1 for message in messages if message["role"] == "user"),
        "messages": messages,
    }

    if session_summary is not None:
        bundle["session_summary"] = session_summary

    return bundle


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def derive_session_fingerprint(assessment: dict[str, Any]) -> str:
    explicit = assessment.get("session_fingerprint")
    if explicit:
        return explicit

    fingerprint_payload = {
        "tool": assessment.get("tool"),
        "session_summary": assessment.get("session_summary"),
        "complexity": assessment.get("complexity"),
        "meaningful_user_messages": assessment.get("meaningful_user_messages"),
        "applicability": assessment.get("applicability", {}),
        "evidence_counts": assessment.get("evidence_counts", {}),
        "dimensions": assessment.get("dimensions", {}),
    }
    digest = hashlib.sha256(canonical_json(fingerprint_payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def session_identity(assessment: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": assessment.get("session_id"),
        "session_fingerprint": derive_session_fingerprint(assessment),
        "model_version": assessment.get("model_version"),
    }


def same_session(record: dict[str, Any], identity: dict[str, Any]) -> bool:
    session_id = identity.get("session_id")
    if session_id and record.get("session_id") == session_id:
        return True

    fingerprint = identity.get("session_fingerprint")
    return bool(fingerprint and record.get("session_fingerprint") == fingerprint)


def load_history(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"sessions": []}
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {
            "sessions": [],
            "_warning": "history_corrupted",
        }


def save_history(path: Path, data: dict[str, Any]) -> None:
    save_json(path, data)


def session_import_path(session_id: str, session_fingerprint: str, imports_dir: Path | None = None) -> Path:
    resolved = imports_dir or resolved_imports_dir()
    base_name = slugify_identifier(session_id)
    candidate = resolved / f"{base_name}.json"
    if not candidate.exists():
        return candidate

    try:
        existing = load_json(candidate)
    except (OSError, json.JSONDecodeError):
        existing = None

    if isinstance(existing, dict) and existing.get("session_id") == session_id:
        return candidate

    return resolved / f"{base_name}-{fingerprint_digest(session_fingerprint)}.json"


def summarize_import_bundle(bundle: dict[str, Any], path: Path) -> dict[str, Any]:
    messages = bundle.get("messages", [])
    if not isinstance(messages, list):
        raise ValueError("import bundle messages must be an array")

    message_count = bundle.get("message_count")
    if not isinstance(message_count, int):
        message_count = len(messages)

    user_message_count = bundle.get("user_message_count")
    if not isinstance(user_message_count, int):
        user_message_count = sum(
            1 for message in messages if isinstance(message, dict) and message.get("role") == "user"
        )

    return {
        "session_id": bundle.get("session_id"),
        "session_fingerprint": bundle.get("session_fingerprint"),
        "tool": bundle.get("tool"),
        "model_version": bundle.get("model_version"),
        "session_summary": bundle.get("session_summary"),
        "source_path": bundle.get("source_path"),
        "imported_at": bundle.get("imported_at"),
        "message_count": message_count,
        "user_message_count": user_message_count,
        "path": str(path),
    }


def load_import_index(imports_dir: Path | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    resolved = imports_dir or resolved_imports_dir()
    if not resolved.exists():
        return [], []

    summaries: list[tuple[int, dict[str, Any]]] = []
    warnings: list[str] = []

    for path in sorted(resolved.glob("*.json")):
        try:
            bundle = load_json(path)
            if not isinstance(bundle, dict):
                raise ValueError("import bundle must be an object")
            summaries.append((path.stat().st_mtime_ns, summarize_import_bundle(bundle, path)))
        except (OSError, json.JSONDecodeError, ValueError):
            warnings.append(path.name)

    summaries.sort(key=lambda item: (item[0], item[1].get("session_id") or ""), reverse=True)
    return [item[1] for item in summaries], warnings


def import_session(payload: Any, source_path: Path | None = None) -> dict[str, Any]:
    bundle = normalize_transcript_bundle(payload, source_path=source_path)
    imports_dir = resolved_imports_dir()
    target = session_import_path(bundle["session_id"], bundle["session_fingerprint"], imports_dir)
    import_write = "updated_existing" if target.exists() else "saved_new"
    save_json(target, bundle)

    result = summarize_import_bundle(bundle, target)
    result["import_path"] = result.pop("path")
    result["import_write"] = import_write
    return result


def list_imports(imports_dir: Path | None = None) -> dict[str, Any]:
    resolved = imports_dir or resolved_imports_dir()
    imports, warnings = load_import_index(resolved)
    latest = imports[0] if imports else None
    return {
        "imports_path": str(resolved),
        "imports_exists": resolved.exists(),
        "import_session_count": len(imports),
        "imports_warning": "imports_unreadable" if warnings else None,
        "unreadable_imports": warnings,
        "latest_session_id": latest.get("session_id") if latest else None,
        "latest_import_path": latest.get("path") if latest else None,
        "imports": imports,
    }


def load_import_bundle(import_path: Path) -> dict[str, Any]:
    bundle = load_json(import_path)
    if not isinstance(bundle, dict):
        raise ValueError("import bundle must be an object")
    return bundle


def resolve_promptiq_version() -> str:
    explicit = os.environ.get("PROMPTIQ_VERSION")
    if explicit and explicit.strip():
        return explicit.strip()

    package_path = Path(__file__).resolve().parents[1] / "package.json"
    if package_path.exists():
        try:
            package_json = load_json(package_path)
        except (OSError, json.JSONDecodeError):
            package_json = None
        if isinstance(package_json, dict):
            version = package_json.get("version")
            if isinstance(version, str) and version.strip():
                return version.strip()

    return "0.0.0"


def resolve_import_bundle(
    session_id: str | None = None,
    import_path: Path | None = None,
    imports_dir: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    if import_path is not None:
        resolved_path = import_path.expanduser()
        if not resolved_path.exists():
            raise ValueError(f"import file not found: {resolved_path}")
        return load_import_bundle(resolved_path), resolved_path

    imports_report = list_imports(imports_dir)
    normalized_session_id = session_id.strip() if isinstance(session_id, str) else None
    if not normalized_session_id or normalized_session_id == "latest":
        latest_path = imports_report.get("latest_import_path")
        if latest_path is None:
            raise ValueError("no imported sessions found. Run import-session first.")
        resolved_path = Path(latest_path)
        return load_import_bundle(resolved_path), resolved_path

    matches = [
        item
        for item in imports_report["imports"]
        if item.get("session_id") == normalized_session_id or item.get("session_fingerprint") == normalized_session_id
    ]
    if not matches:
        raise ValueError(f"imported session not found: {normalized_session_id}")

    match_path = Path(matches[0]["path"])
    return load_import_bundle(match_path), match_path


def replay_messages(bundle: dict[str, Any], include_assistant: bool = False) -> list[dict[str, Any]]:
    raw_messages = bundle.get("messages", [])
    if not isinstance(raw_messages, list):
        raise ValueError("import bundle messages must be an array")

    messages: list[dict[str, Any]] = []
    for index, message in enumerate(raw_messages, start=1):
        if not isinstance(message, dict):
            raise ValueError("import bundle messages must contain objects")
        role = normalize_message_role(message.get("role"))
        if not include_assistant and role != "user":
            continue
        messages.append(
            {
                "turn": index,
                "role": role,
                "content": normalize_message_content(message.get("content")),
            }
        )
    return messages


def replay_metadata(bundle: dict[str, Any], import_path: Path, include_assistant: bool) -> dict[str, Any]:
    summary = summarize_import_bundle(bundle, import_path)
    summary["replay_view"] = "full_transcript" if include_assistant else "user_only"
    return summary


def fallback_session_summary(bundle: dict[str, Any]) -> str:
    session_summary = bundle.get("session_summary")
    if isinstance(session_summary, str) and session_summary.strip():
        return session_summary.strip()

    messages = bundle.get("messages", [])
    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue
            if normalize_message_role(message.get("role")) != "user":
                continue
            content = normalize_message_content(message.get("content"))
            if len(content) <= 140:
                return content
            return f"{content[:137].rstrip()}..."

    return "Imported session review"


def render_replay_markdown(bundle: dict[str, Any], import_path: Path, include_assistant: bool = False) -> str:
    metadata = replay_metadata(bundle, import_path, include_assistant)
    transcript = replay_messages(bundle, include_assistant=include_assistant)
    transcript_lines: list[str] = []

    if include_assistant:
        for message in transcript:
            transcript_lines.append(f"[{message['turn']}] {message['role'].title()}")
            transcript_lines.append(message["content"])
            transcript_lines.append("")
    else:
        for ordinal, message in enumerate(transcript, start=1):
            transcript_lines.append(f"[User {ordinal}]")
            transcript_lines.append(message["content"])
            transcript_lines.append("")

    if transcript_lines and transcript_lines[-1] == "":
        transcript_lines.pop()

    lines = [
        "## PromptIQ Session Replay",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Session ID | `{metadata['session_id']}` |",
        f"| Tool | `{metadata['tool'] or 'unknown'}` |",
        f"| Messages | {metadata['message_count']} total / {metadata['user_message_count']} user |",
        f"| View | `{metadata['replay_view']}` |",
        f"| Imported At | `{metadata['imported_at'] or 'unknown'}` |",
        f"| Source | `{metadata['source_path'] or metadata['path']}` |",
    ]

    session_summary = metadata.get("session_summary")
    if session_summary:
        lines.extend(["", "**Session Summary**", "", session_summary])

    lines.extend(
        [
            "",
            "**Transcript**",
            "",
            "```text",
            *transcript_lines,
            "```",
        ]
    )

    if not include_assistant:
        lines.extend(
            [
                "",
                "PromptIQ scores user steering, so this replay view intentionally shows only user turns.",
            ]
        )

    return "\n".join(lines)


def replay_session(
    session_id: str | None = None,
    import_path: Path | None = None,
    include_assistant: bool = False,
) -> dict[str, Any]:
    bundle, resolved_path = resolve_import_bundle(session_id=session_id, import_path=import_path)
    metadata = replay_metadata(bundle, resolved_path, include_assistant)
    transcript = replay_messages(bundle, include_assistant=include_assistant)
    return {
        **metadata,
        "messages": transcript,
        "markdown": render_replay_markdown(bundle, resolved_path, include_assistant=include_assistant),
    }


def draft_assessment(
    session_id: str | None = None,
    import_path: Path | None = None,
) -> dict[str, Any]:
    bundle, resolved_path = resolve_import_bundle(session_id=session_id, import_path=import_path)
    replay = replay_session(
        import_path=resolved_path,
        include_assistant=False,
    )
    prefilled_summary = fallback_session_summary(bundle)
    user_turn_count = replay["user_message_count"]

    return {
        "source": {
            "session_id": replay["session_id"],
            "session_fingerprint": replay["session_fingerprint"],
            "tool": replay["tool"],
            "model_version": replay["model_version"],
            "import_path": str(resolved_path),
            "source_path": replay["source_path"],
            "imported_at": replay["imported_at"],
        },
        "message_stats": {
            "message_count": replay["message_count"],
            "user_message_count": replay["user_message_count"],
        },
        "notes": [
            "Review only user messages. Evaluate steering quality, not assistant quality.",
            "meaningful_user_messages is prefilled from imported user turns; lower it if some turns are filler rather than real steering.",
            "Fill in complexity, applicability, evidence counts, and dimension scores before calling finalize.",
        ],
        "assessment_template": {
            "date": iso_date(),
            "plugin_version": resolve_promptiq_version(),
            "session_id": replay["session_id"],
            "session_fingerprint": replay["session_fingerprint"],
            "model_version": replay["model_version"],
            "tool": replay["tool"] or "imported",
            "session_summary": prefilled_summary,
            "complexity": "[set: low | medium | high]",
            "meaningful_user_messages": user_turn_count,
            "applicability": {
                "examples": "[set: true | false]",
                "reasoning": "[set: true | false]",
                "tool_awareness": "[set: true | false]",
                "verification": "[set: true | false]",
            },
            "evidence_counts": {
                "evidence_quotes": "[set integer]",
                "corrections_or_refinements": "[set integer]",
                "output_constraints": "[set integer]",
                "tool_signals": "[set integer]",
                "verification_signals": "[set integer]",
            },
            "dimensions": {
                "clarity": "[score 1-10]",
                "context": "[score 1-10]",
                "iteration": "[score 1-10]",
                "decomposition": "[score 1-10]",
                "output_spec": "[score 1-10]",
                "examples": "[score 1-10 or null]",
                "reasoning": "[score 1-10 or null]",
                "tool_awareness": "[score 1-10 or null]",
            },
        },
        "replay_markdown": replay["markdown"],
    }


def import_review_artifact_paths(session_id: str, session_fingerprint: str) -> dict[str, Path]:
    temp_root = Path(tempfile.gettempdir())
    token = slugify_identifier(f"{session_id}-{fingerprint_digest(session_fingerprint)}")
    return {
        "assessment": temp_root / f"promptiq-import-review-{token}-assessment.json",
        "replay": temp_root / f"promptiq-import-review-{token}-replay.md",
    }


def import_review_finalize_command(assessment_path: Path, command_name: str = "score-import") -> str:
    return (
        f'"${{PROMPTIQ_HOME:-$HOME/.promptiq}}/promptiq" {command_name} '
        f'--assessment-file "{assessment_path}" --save'
    )


def prepare_import_review(
    session_id: str | None = None,
    import_path: Path | None = None,
) -> dict[str, Any]:
    draft = draft_assessment(session_id=session_id, import_path=import_path)
    template = draft["assessment_template"]
    source = draft["source"]
    paths = import_review_artifact_paths(template["session_id"], template["session_fingerprint"])

    save_json(paths["assessment"], template)
    paths["replay"].parent.mkdir(parents=True, exist_ok=True)
    paths["replay"].write_text(draft["replay_markdown"], encoding="utf-8")

    return {
        **draft,
        "assessment_file": str(paths["assessment"]),
        "replay_file": str(paths["replay"]),
        "next_command": import_review_finalize_command(paths["assessment"], command_name="score-import"),
        "notes": draft["notes"]
        + [
            "Edit the assessment_file in place, then run next_command to finalize the imported review.",
        ],
    }


def score_import(
    rubric: dict[str, Any],
    save: bool,
    session_id: str | None = None,
    import_path: Path | None = None,
    assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if assessment is None:
        prepared = prepare_import_review(session_id=session_id, import_path=import_path)
        prepared["mode"] = "prepare"
        return prepared

    finalized = finalize(assessment, rubric, save)
    finalized["mode"] = "finalized"
    return finalized


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
    applicability = assessment.get("applicability", {})
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
        if applicability.get("verification") and int(evidence.get("verification_signals", 0)) < 1:
            requirements.append("State how the result will be tested, checked, or falsified instead of assuming the first answer is correct.")

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
        if applicability.get("verification") and int(evidence.get("verification_signals", 0)) < 1:
            requirements.append("Elite scores require at least one explicit verification path so the result can be proven, not merely asserted.")

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


def compute_trend(history: dict[str, Any], rubric_version: str, total: float, identity: dict[str, Any] | None = None) -> dict[str, Any] | None:
    sessions = compatible_sessions(history, rubric_version)
    if identity is not None:
        sessions = [session for session in sessions if not same_session(session, identity)]
    if not sessions:
        return None
    last = sessions[-1]
    last_total = float(last["total"])
    return {
        "last_total": round1(last_total),
        "delta": round1(total - last_total),
        "session_count": len(sessions) + 1
    }


def upsert_session_record(history: dict[str, Any], session_record: dict[str, Any]) -> str:
    sessions = history.setdefault("sessions", [])
    identity = {
        "session_id": session_record.get("session_id"),
        "session_fingerprint": session_record.get("session_fingerprint"),
    }

    for index, existing in enumerate(sessions):
        if existing.get("rubric_version") != session_record.get("rubric_version"):
            continue
        if same_session(existing, identity):
            sessions[index] = session_record
            return "updated_existing"

    sessions.append(session_record)
    return "saved_new"


def doctor(helper_path: Path, rubric_path: Path) -> dict[str, Any]:
    helper = helper_path.expanduser()
    rubric_file = rubric_path.expanduser()
    issues: list[str] = []
    rubric_version: str | None = None
    rubric_error: str | None = None
    history_file = resolved_history_path()

    helper_exists = helper.exists()
    if not helper_exists:
        issues.append("helper_missing")
    launcher_path = resolved_launcher_path()
    launcher_exists = launcher_path.exists()
    bin_launcher_path = resolved_bin_launcher_path()
    bin_launcher_exists = bin_launcher_path.exists()
    launcher_in_path = shutil.which("promptiq") is not None

    rubric_exists = rubric_file.exists()
    if not rubric_exists:
        issues.append("rubric_missing")
    else:
        try:
            rubric = load_json(rubric_file)
        except (OSError, json.JSONDecodeError) as exc:
            rubric_error = str(exc)
            issues.append("rubric_unreadable")
        else:
            rubric_version = rubric.get("rubric_version")
            history_file = history_path(rubric)

    history = load_history(history_file)
    imports_report = list_imports()
    history_warning = history.get("_warning")
    if history_warning == "history_corrupted":
        issues.append("history_corrupted")

    if any(issue in {"helper_missing", "rubric_missing", "rubric_unreadable"} for issue in issues):
        status = "action_needed"
        next_step = "Run /install to restore the local helper files."
    elif "history_corrupted" in issues:
        status = "warning"
        next_step = "Run /score once to recreate clean local history."
    else:
        status = "ok"
        next_step = "PromptIQ is ready. Run /score after a real working session."

    return {
        "status": status,
        "issues": issues,
        "next_step": next_step,
        "promptiq_home": str(resolve_promptiq_home()),
        "helper_path": str(helper),
        "helper_exists": helper_exists,
        "launcher_path": str(launcher_path),
        "launcher_exists": launcher_exists,
        "bin_launcher_path": str(bin_launcher_path),
        "bin_launcher_exists": bin_launcher_exists,
        "launcher_in_path": launcher_in_path,
        "rubric_path": str(rubric_file),
        "rubric_exists": rubric_exists,
        "rubric_version": rubric_version,
        "rubric_error": rubric_error,
        "history_path": str(history_file),
        "history_exists": history_file.exists(),
        "history_session_count": len(history.get("sessions", [])),
        "history_warning": history_warning,
        "imports_path": imports_report["imports_path"],
        "imports_exists": imports_report["imports_exists"],
        "import_session_count": imports_report["import_session_count"],
        "imports_warning": imports_report["imports_warning"],
    }


def finalize(assessment: dict[str, Any], rubric: dict[str, Any], save: bool) -> dict[str, Any]:
    validate_assessment(assessment)
    identity = session_identity(assessment)
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
    trend = compute_trend(history, rubric["rubric_version"], total, identity)

    session_record = {
        "date": assessment["date"],
        "session_id": identity["session_id"],
        "session_fingerprint": identity["session_fingerprint"],
        "model_version": identity["model_version"],
        "total": total,
        "raw_total": raw_total,
        "complexity": assessment.get("complexity"),
        "confidence": confidence,
        "rubric_version": rubric["rubric_version"],
        "plugin_version": assessment.get("plugin_version"),
        "tool": assessment.get("tool"),
        "meaningful_user_messages": assessment.get("meaningful_user_messages"),
        "evidence_counts": assessment.get("evidence_counts", {}),
        "evidence": assessment.get("evidence", {}),
        "cap_reasons": cap_reasons,
        "score_band": band,
        "weakest_dimension": weakest,
        "dimensions": dimensions,
        "applicability": assessment.get("applicability", {}),
        "session_summary": assessment.get("session_summary", ""),
    }

    analytics_records = [
        record
        for record in compatible_sessions(history, rubric["rubric_version"])
        if not same_session(record, identity)
    ] + [session_record]
    session_count = len(analytics_records)
    recent_trend = recent_trend_entries(analytics_records)
    weakest_focus_area = focus_area(analytics_records)
    history_write = "not_saved"

    if save:
        history_write = upsert_session_record(history, session_record)
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
        "history_write": history_write,
        "trend": trend,
        "session_record": session_record,
        "evidence": assessment.get("evidence", {}),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["doctor", "finalize", "import-session", "list-imports", "replay-session", "draft-assessment", "prepare-import-review", "score-import"])
    parser.add_argument("--assessment-json")
    parser.add_argument("--assessment-file")
    parser.add_argument("--session-json")
    parser.add_argument("--session-file")
    parser.add_argument("--session-id")
    parser.add_argument("--import-path")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--include-assistant", action="store_true")
    parser.add_argument("--rubric", default=str(Path(__file__).with_name(DEFAULT_RUBRIC_FILENAME)))
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.command == "doctor":
            result = doctor(Path(__file__), Path(args.rubric))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.command == "import-session":
            source_path = Path(args.session_file).expanduser() if args.session_file else None
            session_payload = load_session_payload(args.session_json, args.session_file)
            result = import_session(session_payload, source_path=source_path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.command == "list-imports":
            result = list_imports()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.command == "replay-session":
            import_path = Path(args.import_path).expanduser() if args.import_path else None
            result = replay_session(
                session_id=args.session_id,
                import_path=import_path,
                include_assistant=args.include_assistant,
            )
            if args.format == "markdown":
                print(result["markdown"])
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.command == "draft-assessment":
            import_path = Path(args.import_path).expanduser() if args.import_path else None
            result = draft_assessment(
                session_id=args.session_id,
                import_path=import_path,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.command == "prepare-import-review":
            import_path = Path(args.import_path).expanduser() if args.import_path else None
            result = prepare_import_review(
                session_id=args.session_id,
                import_path=import_path,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.command == "score-import":
            import_path = Path(args.import_path).expanduser() if args.import_path else None
            assessment = None
            rubric: dict[str, Any] = {}
            if args.assessment_json is not None or args.assessment_file is not None:
                assessment = load_assessment_payload(args.assessment_json, args.assessment_file)
                rubric = load_json(Path(args.rubric))
            result = score_import(
                rubric,
                save=args.save,
                session_id=args.session_id,
                import_path=import_path,
                assessment=assessment,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        assessment = load_assessment_payload(args.assessment_json, args.assessment_file)
        rubric = load_json(Path(args.rubric))
        if args.command == "finalize":
            result = finalize(assessment, rubric, args.save)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except PermissionError as exc:
        target = exc.filename or "the requested path"
        print(
            f"PromptIQ command failed: permission denied while writing to {target}. "
            "Set PROMPTIQ_HOME or PROMPTIQ_IMPORTS_PATH to a writable location and try again.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"PromptIQ command failed: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
