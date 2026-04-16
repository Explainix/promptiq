import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
import importlib.util
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / 'skills' / 'score' / 'scripts' / 'promptiq.py'
RUBRIC_PATH = ROOT / 'skills' / 'score' / 'scripts' / 'rubric_v1.json'


def load_engine():
    spec = importlib.util.spec_from_file_location('promptiq_engine', ENGINE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ENGINE = load_engine()
RUBRIC = json.loads(RUBRIC_PATH.read_text())


def make_assessment(**overrides):
    assessment = {
        'date': '2026-04-13',
        'plugin_version': '1.0.0',
        'tool': 'codex',
        'session_summary': 'prototype session',
        'complexity': 'medium',
        'meaningful_user_messages': 6,
        'applicability': {
            'examples': False,
            'reasoning': True,
            'tool_awareness': True,
            'verification': False,
        },
        'evidence_counts': {
            'evidence_quotes': 2,
            'corrections_or_refinements': 1,
            'output_constraints': 1,
            'tool_signals': 1,
            'verification_signals': 0,
        },
        'dimensions': {
            'clarity': 7.0,
            'context': 7.0,
            'iteration': 7.0,
            'decomposition': 7.0,
            'output_spec': 7.0,
            'examples': None,
            'reasoning': 7.0,
            'tool_awareness': 7.0,
        },
    }
    assessment.update(overrides)
    return assessment


class PromptIQEngineTests(unittest.TestCase):
    def test_load_assessment_payload_supports_file_input(self):
        payload = make_assessment()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'assessment.json'
            path.write_text(json.dumps(payload))
            loaded = ENGINE.load_assessment_payload(None, str(path))

        self.assertEqual(loaded['session_summary'], payload['session_summary'])

    def test_load_assessment_payload_rejects_ambiguous_input(self):
        with self.assertRaises(ValueError):
            ENGINE.load_assessment_payload('{"date":"2026-04-13"}', '/tmp/input.json')

    def test_load_session_payload_supports_file_input(self):
        payload = {'transcript': [{'role': 'user', 'content': 'hello'}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'session.json'
            path.write_text(json.dumps(payload))
            loaded = ENGINE.load_session_payload(None, str(path))

        self.assertEqual(loaded['transcript'][0]['content'], 'hello')

    def test_load_session_payload_rejects_ambiguous_input(self):
        with self.assertRaises(ValueError):
            ENGINE.load_session_payload('{"messages":[]}', '/tmp/session.json')

    def test_load_history_recovers_from_corrupted_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'history.json'
            path.write_text('{broken')
            history = ENGINE.load_history(path)

        self.assertEqual(history['sessions'], [])
        self.assertEqual(history['_warning'], 'history_corrupted')

    def test_short_session_is_capped(self):
        assessment = make_assessment(
            complexity='low',
            meaningful_user_messages=2,
            evidence_counts={
                'evidence_quotes': 1,
                'corrections_or_refinements': 0,
                'output_constraints': 0,
                'tool_signals': 0,
                'verification_signals': 0,
            },
            dimensions={
                'clarity': 9.0,
                'context': 8.0,
                'iteration': 8.0,
                'decomposition': 7.0,
                'output_spec': 8.0,
                'examples': None,
                'reasoning': None,
                'tool_awareness': None,
            },
        )

        result = ENGINE.finalize(assessment, copy.deepcopy(RUBRIC), save=False)

        self.assertEqual(result['confidence'], 'low')
        self.assertEqual(result['total'], 6.4)
        self.assertIn('short_session_cap', result['cap_reasons'])
        self.assertEqual(result['score_band'], 'foundational')
        self.assertTrue(any('too short' in reason.lower() for reason in result['why_not_higher']))

    def test_gate_blocks_scores_above_7_5_without_evidence(self):
        assessment = make_assessment(
            complexity='high',
            meaningful_user_messages=8,
            evidence_counts={
                'evidence_quotes': 1,
                'corrections_or_refinements': 0,
                'output_constraints': 0,
                'tool_signals': 0,
                'verification_signals': 0,
            },
            dimensions={
                'clarity': 8.0,
                'context': 8.0,
                'iteration': 8.0,
                'decomposition': 8.0,
                'output_spec': 8.0,
                'examples': None,
                'reasoning': 8.0,
                'tool_awareness': 8.0,
            },
        )

        result = ENGINE.finalize(assessment, copy.deepcopy(RUBRIC), save=False)

        self.assertEqual(result['confidence'], 'medium')
        self.assertEqual(result['total'], 7.4)
        self.assertIn('above_7_5_gate_failed', result['cap_reasons'])
        self.assertEqual(result['score_band'], 'competent')
        self.assertEqual(result['next_band']['target_total'], 7.5)

    def test_elite_session_can_clear_the_high_bar(self):
        assessment = make_assessment(
            complexity='high',
            meaningful_user_messages=9,
            applicability={
                'examples': False,
                'reasoning': True,
                'tool_awareness': True,
                'verification': True,
            },
            evidence_counts={
                'evidence_quotes': 4,
                'corrections_or_refinements': 2,
                'output_constraints': 2,
                'tool_signals': 1,
                'verification_signals': 1,
            },
            dimensions={
                'clarity': 9.0,
                'context': 8.5,
                'iteration': 9.0,
                'decomposition': 8.5,
                'output_spec': 9.0,
                'examples': None,
                'reasoning': 8.5,
                'tool_awareness': 8.5,
            },
        )

        result = ENGINE.finalize(assessment, copy.deepcopy(RUBRIC), save=False)

        self.assertEqual(result['confidence'], 'high')
        self.assertEqual(result['total'], 8.7)
        self.assertEqual(result['score_band'], 'elite')
        self.assertEqual(result['cap_reasons'], [])
        self.assertIsNone(result['next_band'])

    def test_high_score_requires_verification_when_applicable(self):
        assessment = make_assessment(
            complexity='high',
            meaningful_user_messages=8,
            applicability={
                'examples': False,
                'reasoning': True,
                'tool_awareness': True,
                'verification': True,
            },
            evidence_counts={
                'evidence_quotes': 2,
                'corrections_or_refinements': 1,
                'output_constraints': 1,
                'tool_signals': 1,
                'verification_signals': 0,
            },
            dimensions={
                'clarity': 8.0,
                'context': 8.0,
                'iteration': 8.0,
                'decomposition': 8.0,
                'output_spec': 8.0,
                'examples': None,
                'reasoning': 8.0,
                'tool_awareness': 8.0,
            },
        )

        result = ENGINE.finalize(assessment, copy.deepcopy(RUBRIC), save=False)

        self.assertEqual(result['total'], 7.4)
        self.assertIn('above_7_5_gate_failed', result['cap_reasons'])
        self.assertTrue(
            any('tested, checked, or falsified' in reason for reason in result['why_not_higher'])
        )

    def test_recent_trend_and_focus_area_include_current_session(self):
        rubric = copy.deepcopy(RUBRIC)
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / 'history.json'
            history_file.write_text(
                json.dumps(
                    {
                        'sessions': [
                            {
                                'date': '2026-04-10',
                                'total': 6.0,
                                'rubric_version': rubric['rubric_version'],
                                'dimensions': {
                                    'clarity': 6.0,
                                    'context': 5.0,
                                    'iteration': 6.0,
                                    'decomposition': 6.0,
                                    'output_spec': 5.0,
                                    'examples': None,
                                    'reasoning': 6.0,
                                    'tool_awareness': 6.0,
                                },
                            },
                            {
                                'date': '2026-04-12',
                                'total': 7.1,
                                'rubric_version': rubric['rubric_version'],
                                'dimensions': {
                                    'clarity': 7.0,
                                    'context': 6.0,
                                    'iteration': 7.0,
                                    'decomposition': 7.0,
                                    'output_spec': 6.0,
                                    'examples': None,
                                    'reasoning': 7.0,
                                    'tool_awareness': 7.0,
                                },
                            },
                        ]
                    }
                )
            )
            rubric['history']['path'] = str(history_file)

            result = ENGINE.finalize(make_assessment(), rubric, save=False)

        self.assertEqual(result['history_session_count'], 3)
        self.assertEqual(len(result['recent_trend']), 3)
        self.assertEqual(result['recent_trend'][-1]['date'], '2026-04-13')
        self.assertIsNotNone(result['focus_area'])
        self.assertEqual(result['focus_area']['key'], 'context')

    def test_duplicate_session_updates_history_in_place(self):
        rubric = copy.deepcopy(RUBRIC)
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / 'history.json'
            history_file.write_text(
                json.dumps(
                    {
                        'sessions': [
                            {
                                'date': '2026-04-12',
                                'session_id': 'sess-123',
                                'session_fingerprint': 'sha256:old',
                                'model_version': 'gpt-5.2',
                                'total': 7.1,
                                'raw_total': 7.1,
                                'complexity': 'high',
                                'confidence': 'medium',
                                'rubric_version': rubric['rubric_version'],
                                'plugin_version': '1.0.0',
                                'tool': 'codex',
                                'meaningful_user_messages': 6,
                                'evidence_counts': {'evidence_quotes': 2},
                                'cap_reasons': [],
                                'score_band': 'competent',
                                'weakest_dimension': {'key': 'context', 'label': 'Context Provision', 'score': 6.0},
                                'dimensions': {
                                    'clarity': 7.0,
                                    'context': 6.0,
                                    'iteration': 7.0,
                                    'decomposition': 7.0,
                                    'output_spec': 7.0,
                                    'examples': None,
                                    'reasoning': 7.0,
                                    'tool_awareness': 7.0,
                                },
                                'applicability': {
                                    'examples': False,
                                    'reasoning': True,
                                    'tool_awareness': True,
                                    'verification': True,
                                },
                                'session_summary': 'same session',
                            }
                        ]
                    }
                )
            )
            rubric['history']['path'] = str(history_file)

            assessment = make_assessment(
                session_id='sess-123',
                model_version='gpt-5.4',
                session_summary='same session',
                applicability={
                    'examples': False,
                    'reasoning': True,
                    'tool_awareness': True,
                    'verification': True,
                },
                evidence_counts={
                    'evidence_quotes': 3,
                    'corrections_or_refinements': 1,
                    'output_constraints': 1,
                    'tool_signals': 1,
                    'verification_signals': 1,
                },
            )

            result = ENGINE.finalize(assessment, rubric, save=True)
            stored = json.loads(history_file.read_text())

        self.assertEqual(result['history_write'], 'updated_existing')
        self.assertEqual(result['history_session_count'], 1)
        self.assertEqual(len(stored['sessions']), 1)
        self.assertEqual(stored['sessions'][0]['session_id'], 'sess-123')
        self.assertEqual(stored['sessions'][0]['model_version'], 'gpt-5.4')
        self.assertEqual(stored['sessions'][0]['total'], result['total'])

    def test_trend_ignores_same_session_reassessment(self):
        rubric = copy.deepcopy(RUBRIC)
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / 'history.json'
            history_file.write_text(
                json.dumps(
                    {
                        'sessions': [
                            {
                                'date': '2026-04-10',
                                'session_id': 'sess-older',
                                'session_fingerprint': 'sha256:older',
                                'total': 6.2,
                                'rubric_version': rubric['rubric_version'],
                            },
                            {
                                'date': '2026-04-12',
                                'session_id': 'sess-current',
                                'session_fingerprint': 'sha256:current',
                                'total': 7.1,
                                'rubric_version': rubric['rubric_version'],
                            },
                        ]
                    }
                )
            )
            rubric['history']['path'] = str(history_file)

            result = ENGINE.finalize(
                make_assessment(
                    session_id='sess-current',
                    session_summary='current session rescored',
                ),
                rubric,
                save=False,
            )

        self.assertIsNotNone(result['trend'])
        self.assertEqual(result['trend']['last_total'], 6.2)
        self.assertEqual(result['trend']['delta'], 0.8)

    def test_trend_only_uses_same_rubric_version(self):
        rubric = copy.deepcopy(RUBRIC)
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / 'history.json'
            history_file.write_text(
                json.dumps(
                    {
                        'sessions': [
                            {
                                'date': '2026-04-10',
                                'total': 5.9,
                                'rubric_version': '0.9.0',
                            },
                            {
                                'date': '2026-04-12',
                                'total': 7.1,
                                'rubric_version': rubric['rubric_version'],
                            },
                        ]
                    }
                )
            )
            rubric['history']['path'] = str(history_file)

            result = ENGINE.finalize(make_assessment(), rubric, save=False)

        self.assertIsNotNone(result['trend'])
        self.assertEqual(result['trend']['last_total'], 7.1)
        self.assertEqual(result['trend']['delta'], -0.1)

    def test_history_path_uses_promptiq_home_override(self):
        rubric = copy.deepcopy(RUBRIC)
        with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': '/tmp/custom-promptiq'}, clear=False):
            path = ENGINE.history_path(rubric)

        self.assertEqual(path, Path('/tmp/custom-promptiq/history.json'))

    def test_history_path_prefers_explicit_history_override(self):
        rubric = copy.deepcopy(RUBRIC)
        with patch.dict(
            ENGINE.os.environ,
            {
                'PROMPTIQ_HOME': '/tmp/custom-promptiq',
                'PROMPTIQ_HISTORY_PATH': '/tmp/promptiq-state/history.json',
            },
            clear=False,
        ):
            path = ENGINE.history_path(rubric)

        self.assertEqual(path, Path('/tmp/promptiq-state/history.json'))

    def test_doctor_reports_ready_installation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            helper = root / 'promptiq.py'
            launcher = root / 'promptiq'
            rubric_path = root / 'rubric_v1.json'
            history_file = root / 'history.json'
            bin_dir = root / 'bin'
            bin_launcher = bin_dir / 'promptiq'

            helper.write_text('#!/usr/bin/env python3\n', encoding='utf-8')
            launcher.write_text('#!/bin/sh\n', encoding='utf-8')
            rubric_path.write_text(json.dumps(RUBRIC), encoding='utf-8')
            history_file.write_text(
                json.dumps({'sessions': [{'total': 7.0, 'rubric_version': RUBRIC['rubric_version']}]})
            )
            bin_dir.mkdir(parents=True)
            bin_launcher.write_text('#!/bin/sh\n', encoding='utf-8')

            def fake_which(name: str):
                if name == 'promptiq':
                    return str(bin_launcher)
                return None

            with patch.dict(
                ENGINE.os.environ,
                {
                    'PROMPTIQ_HOME': str(root),
                    'PROMPTIQ_BIN_DIR': str(bin_dir),
                },
                clear=False,
            ):
                with patch.object(ENGINE.shutil, 'which', side_effect=fake_which):
                    report = ENGINE.doctor(helper, rubric_path)

        self.assertEqual(report['status'], 'ok')
        self.assertEqual(report['history_session_count'], 1)
        self.assertEqual(report['rubric_version'], RUBRIC['rubric_version'])
        self.assertEqual(report['issues'], [])
        self.assertEqual(report['launcher_path'], str(launcher))
        self.assertTrue(report['launcher_exists'])
        self.assertEqual(report['bin_launcher_path'], str(bin_launcher))
        self.assertTrue(report['bin_launcher_exists'])
        self.assertTrue(report['launcher_in_path'])

    def test_doctor_flags_corrupted_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            helper = root / 'promptiq.py'
            rubric_path = root / 'rubric_v1.json'
            history_file = root / 'history.json'

            helper.write_text('#!/usr/bin/env python3\n', encoding='utf-8')
            rubric_path.write_text(json.dumps(RUBRIC), encoding='utf-8')
            history_file.write_text('{broken', encoding='utf-8')

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                report = ENGINE.doctor(helper, rubric_path)

        self.assertEqual(report['status'], 'warning')
        self.assertIn('history_corrupted', report['issues'])
        self.assertEqual(report['history_warning'], 'history_corrupted')

    def test_validation_rejects_unknown_dimension(self):
        assessment = make_assessment()
        assessment['dimensions'] = dict(assessment['dimensions'])
        assessment['dimensions']['style'] = 9

        with self.assertRaises(ValueError):
            ENGINE.finalize(assessment, copy.deepcopy(RUBRIC), save=False)

    def test_validation_requires_applicability_keys(self):
        assessment = make_assessment()
        assessment['applicability'] = {'examples': True}

        with self.assertRaises(ValueError):
            ENGINE.finalize(assessment, copy.deepcopy(RUBRIC), save=False)

    def test_validate_assessment_accepts_evidence_field(self):
        """evidence field is optional but when present must be a dict of dimension -> string."""
        base = make_assessment()
        base["evidence"] = {
            "clarity": "Third prompt did not specify expected output format",
            "context": "Provided file path and error message at session start",
        }
        # should not raise
        ENGINE.validate_assessment(base)

    def test_validate_assessment_rejects_non_string_evidence_value(self):
        base = make_assessment()
        base["evidence"] = {"clarity": 42}
        with self.assertRaises(ValueError, msg="evidence"):
            ENGINE.validate_assessment(base)

    def test_validate_assessment_rejects_unknown_dimension_in_evidence(self):
        base = make_assessment()
        base["evidence"] = {"nonexistent_dim": "some text"}
        with self.assertRaises(ValueError, msg="evidence"):
            ENGINE.validate_assessment(base)

    def test_finalize_includes_evidence_in_output(self):
        assessment = make_assessment()
        assessment["evidence"] = {
            "clarity": "Third prompt did not specify expected output format",
        }
        result = ENGINE.finalize(assessment, copy.deepcopy(RUBRIC), save=False)
        self.assertIn("evidence", result)
        self.assertEqual(result["evidence"]["clarity"], "Third prompt did not specify expected output format")

    def test_finalize_evidence_absent_when_not_provided(self):
        assessment = make_assessment()
        result = ENGINE.finalize(assessment, copy.deepcopy(RUBRIC), save=False)
        self.assertEqual(result.get("evidence"), {})

    def test_apply_caps_no_evidence_cap(self):
        """Dimension score > 5 without evidence sentence should cap total at 5."""
        assessment = make_assessment()
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
        assessment["evidence"] = {}
        raw_total = 5.6
        confidence = "medium"
        rubric = copy.deepcopy(RUBRIC)
        total, cap_reasons = ENGINE.apply_caps(raw_total, assessment, rubric, confidence)
        self.assertIn("no_evidence_cap", cap_reasons)

    def test_apply_caps_no_evidence_cap_not_triggered_when_evidence_present(self):
        assessment = make_assessment()
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
        rubric = copy.deepcopy(RUBRIC)
        total, cap_reasons = ENGINE.apply_caps(raw_total, assessment, rubric, confidence)
        self.assertNotIn("no_evidence_cap", cap_reasons)


    def test_recent_trend_entries_includes_dimension_deltas(self):
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
        entries = ENGINE.recent_trend_entries(records)
        self.assertEqual(len(entries), 2)
        second = entries[1]
        self.assertIn("dimension_deltas", second)
        self.assertEqual(second["dimension_deltas"]["clarity"], 2.0)
        self.assertEqual(second["dimension_deltas"]["context"], 0.0)

    def test_recent_trend_entries_first_entry_has_no_deltas(self):
        records = [
            {
                "date": "2026-04-10",
                "total": 6.0,
                "dimensions": {"clarity": 5, "context": 6, "iteration": 5,
                               "decomposition": 5, "output_spec": 5,
                               "examples": None, "reasoning": None, "tool_awareness": None},
            },
        ]
        entries = ENGINE.recent_trend_entries(records)
        self.assertIsNone(entries[0].get("dimension_deltas"))

    def test_detect_milestone_at_5(self):
        self.assertEqual(ENGINE.detect_milestone(5), {"session_count": 5, "message": "5 sessions in."})

    def test_detect_milestone_at_10(self):
        result = ENGINE.detect_milestone(10)
        self.assertIsNotNone(result)
        self.assertEqual(result["session_count"], 10)

    def test_detect_milestone_none_at_non_milestone(self):
        self.assertIsNone(ENGINE.detect_milestone(3))
        self.assertIsNone(ENGINE.detect_milestone(7))
        self.assertIsNone(ENGINE.detect_milestone(11))


if __name__ == '__main__':
    unittest.main()
