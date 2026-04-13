import copy
import json
import tempfile
import unittest
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / 'engine' / 'promptiq.py'
RUBRIC_PATH = ROOT / 'engine' / 'rubric_v1.json'


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
        },
        'evidence_counts': {
            'evidence_quotes': 2,
            'corrections_or_refinements': 1,
            'output_constraints': 1,
            'tool_signals': 1,
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

    def test_load_history_recovers_from_corrupted_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'history.json'
            path.write_text('{broken')
            history = ENGINE.load_history(path)

        self.assertEqual(history['sessions'], [])
        self.assertEqual(history['_warning'], 'history_corrupted')

    def test_fixture_files_have_minimum_schema(self):
        fixture_dir = ROOT / 'fixtures'
        for path in fixture_dir.glob('*.json'):
            payload = json.loads(path.read_text())
            self.assertIn('name', payload, path.name)
            self.assertIn('description', payload, path.name)
            self.assertIn('expected', payload, path.name)
            self.assertIn('transcript', payload, path.name)
            self.assertIsInstance(payload['transcript'], list, path.name)
            self.assertGreater(len(payload['transcript']), 0, path.name)
            for item in payload['transcript']:
                self.assertIn('role', item, path.name)
                self.assertIn('content', item, path.name)

    def test_short_session_is_capped(self):
        assessment = make_assessment(
            complexity='low',
            meaningful_user_messages=2,
            evidence_counts={
                'evidence_quotes': 1,
                'corrections_or_refinements': 0,
                'output_constraints': 0,
                'tool_signals': 0,
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
            evidence_counts={
                'evidence_quotes': 4,
                'corrections_or_refinements': 2,
                'output_constraints': 2,
                'tool_signals': 1,
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


if __name__ == '__main__':
    unittest.main()
