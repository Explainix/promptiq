import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
import importlib.util
from unittest.mock import patch


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

    def test_normalize_transcript_bundle_accepts_messages_and_text_parts(self):
        bundle = ENGINE.normalize_transcript_bundle(
            {
                'session_id': 'sess-001',
                'tool': 'claude-code',
                'messages': [
                    {
                        'role': 'human',
                        'content': [
                            {'type': 'text', 'text': 'First line'},
                            {'type': 'image', 'url': 'https://example.com/demo.png'},
                            'Second line',
                        ],
                    },
                    {
                        'role': 'assistant',
                        'parts': [{'text': 'Done'}],
                    },
                ],
            }
        )

        self.assertEqual(bundle['session_id'], 'sess-001')
        self.assertEqual(bundle['tool'], 'claude-code')
        self.assertEqual(bundle['messages'][0]['role'], 'user')
        self.assertEqual(bundle['messages'][0]['content'], 'First line\nSecond line')
        self.assertEqual(bundle['messages'][1]['content'], 'Done')
        self.assertEqual(bundle['message_count'], 2)
        self.assertEqual(bundle['user_message_count'], 1)

    def test_import_session_persists_normalized_bundle(self):
        payload = {
            'tool': 'codex',
            'description': 'Imported debug session',
            'transcript': [
                {'role': 'user', 'content': 'Check the build output first.'},
                {'role': 'assistant', 'content': 'I will inspect the logs.'},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / 'import-source.json'
            source.write_text(json.dumps(payload), encoding='utf-8')

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                result = ENGINE.import_session(payload, source_path=source)
                stored = json.loads(Path(result['import_path']).read_text(encoding='utf-8'))

        self.assertEqual(result['import_write'], 'saved_new')
        self.assertEqual(result['tool'], 'codex')
        self.assertEqual(result['message_count'], 2)
        self.assertEqual(result['user_message_count'], 1)
        self.assertTrue(result['session_id'].startswith('import-'))
        self.assertEqual(stored['source_path'], str(source.resolve()))
        self.assertEqual(stored['session_summary'], 'Imported debug session')

    def test_list_imports_and_doctor_report_import_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            helper = root / 'promptiq.py'
            rubric_path = root / 'rubric_v1.json'

            helper.write_text('#!/usr/bin/env python3\n', encoding='utf-8')
            rubric_path.write_text(json.dumps(RUBRIC), encoding='utf-8')

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(
                    [{'role': 'user', 'content': 'First imported session'}],
                )
                ENGINE.import_session(
                    [{'role': 'user', 'content': 'Second imported session'}],
                )
                imports = ENGINE.list_imports()
                doctor = ENGINE.doctor(helper, rubric_path)

        self.assertEqual(imports['import_session_count'], 2)
        self.assertEqual(len(imports['imports']), 2)
        self.assertIsNotNone(imports['latest_session_id'])
        self.assertIsNotNone(imports['latest_import_path'])
        self.assertEqual(doctor['import_session_count'], 2)
        self.assertEqual(doctor['imports_path'], str(root / 'imports'))
        self.assertIsNone(doctor['imports_warning'])

    def test_list_imports_flags_unreadable_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            imports_dir = Path(tmpdir) / 'imports'
            imports_dir.mkdir(parents=True)
            (imports_dir / 'broken.json').write_text('{broken', encoding='utf-8')

            result = ENGINE.list_imports(imports_dir)

        self.assertEqual(result['import_session_count'], 0)
        self.assertEqual(result['imports_warning'], 'imports_unreadable')
        self.assertEqual(result['unreadable_imports'], ['broken.json'])

    def test_main_supports_import_session_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stdout = io.StringIO()

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                with patch('sys.stdout', stdout):
                    ENGINE.main(
                        [
                            'import-session',
                            '--session-json',
                            '[{"role":"user","content":"hello from cli"}]',
                        ]
                    )

                self.assertTrue((root / 'imports').exists())

        result = json.loads(stdout.getvalue())
        self.assertEqual(result['import_write'], 'saved_new')
        self.assertEqual(result['message_count'], 1)

    def test_replay_session_defaults_to_user_only_view(self):
        payload = {
            'session_id': 'sess-replay',
            'tool': 'codex',
            'description': 'Replayable debug session',
            'transcript': [
                {'role': 'user', 'content': 'Check the auth middleware first.'},
                {'role': 'assistant', 'content': 'I will inspect auth.ts.'},
                {'role': 'user', 'content': 'Compare it to yesterday before changing code.'},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(payload)
                replay = ENGINE.replay_session(session_id='sess-replay')

        self.assertEqual(replay['replay_view'], 'user_only')
        self.assertEqual(len(replay['messages']), 2)
        self.assertTrue(all(message['role'] == 'user' for message in replay['messages']))
        self.assertIn('PromptIQ Session Replay', replay['markdown'])
        self.assertNotIn('inspect auth.ts', replay['markdown'])
        self.assertIn('user turns', replay['markdown'])

    def test_replay_session_uses_latest_import_when_identifier_is_omitted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session([{'role': 'user', 'content': 'Older imported session'}])
                latest = ENGINE.import_session([{'role': 'user', 'content': 'Most recent imported session'}])
                replay = ENGINE.replay_session()

        self.assertEqual(replay['session_id'], latest['session_id'])
        self.assertIn('Most recent imported session', replay['markdown'])
        self.assertNotIn('Older imported session', replay['markdown'])

    def test_replay_session_can_render_full_markdown_from_cli(self):
        payload = {
            'session_id': 'sess-full',
            'tool': 'claude-code',
            'messages': [
                {'role': 'user', 'content': 'Find the failing migration.'},
                {'role': 'assistant', 'content': 'I found a mismatch in the schema.'},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stdout = io.StringIO()

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(payload)
                with patch('sys.stdout', stdout):
                    ENGINE.main(
                        [
                            'replay-session',
                            '--session-id',
                            'sess-full',
                            '--include-assistant',
                            '--format',
                            'markdown',
                        ]
                    )

        rendered = stdout.getvalue()
        self.assertIn('## PromptIQ Session Replay', rendered)
        self.assertIn('[1] User', rendered)
        self.assertIn('[2] Assistant', rendered)
        self.assertIn('I found a mismatch in the schema.', rendered)

    def test_replay_session_rejects_missing_identifier(self):
        with self.assertRaises(ValueError):
            ENGINE.replay_session()

    def test_main_reports_replay_errors_cleanly(self):
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': tmpdir}, clear=False):
                with patch('sys.stderr', stderr):
                    with self.assertRaises(SystemExit) as exit_info:
                        ENGINE.main(['replay-session'])

        self.assertEqual(exit_info.exception.code, 1)
        self.assertIn('PromptIQ command failed', stderr.getvalue())
        self.assertIn('no imported sessions found', stderr.getvalue())

    def test_draft_assessment_prefills_import_metadata(self):
        payload = {
            'session_id': 'sess-draft',
            'tool': 'codex',
            'messages': [
                {'role': 'user', 'content': 'Audit the failing auth flow.'},
                {'role': 'assistant', 'content': 'I am checking middleware.'},
                {'role': 'user', 'content': 'Keep the fix minimal and verifiable.'},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(payload)
                draft = ENGINE.draft_assessment(session_id='sess-draft')

        template = draft['assessment_template']
        self.assertEqual(template['session_id'], 'sess-draft')
        self.assertEqual(template['tool'], 'codex')
        self.assertEqual(template['meaningful_user_messages'], 2)
        self.assertEqual(template['plugin_version'], '0.4.0')
        self.assertEqual(template['complexity'], '[set: low | medium | high]')
        self.assertIn('PromptIQ Session Replay', draft['replay_markdown'])
        self.assertEqual(draft['message_stats']['user_message_count'], 2)

    def test_draft_assessment_defaults_to_latest_import(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session([{'role': 'user', 'content': 'First imported session'}])
                latest = ENGINE.import_session(
                    {
                        'session_id': 'sess-latest-draft',
                        'transcript': [{'role': 'user', 'content': 'Use me for the draft'}],
                    }
                )
                draft = ENGINE.draft_assessment()

        self.assertEqual(draft['source']['session_id'], latest['session_id'])
        self.assertEqual(draft['assessment_template']['session_id'], 'sess-latest-draft')

    def test_main_supports_draft_assessment_command(self):
        payload = {
            'session_id': 'sess-cli-draft',
            'transcript': [{'role': 'user', 'content': 'Narrow the investigation to runtime logs.'}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stdout = io.StringIO()

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(payload)
                with patch('sys.stdout', stdout):
                    ENGINE.main(['draft-assessment', '--session-id', 'sess-cli-draft'])

        result = json.loads(stdout.getvalue())
        self.assertEqual(result['assessment_template']['session_id'], 'sess-cli-draft')
        self.assertEqual(result['assessment_template']['meaningful_user_messages'], 1)

    def test_main_supports_draft_assessment_without_session_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stdout = io.StringIO()

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(
                    {
                        'session_id': 'sess-most-recent',
                        'transcript': [{'role': 'user', 'content': 'Score the latest import by default.'}],
                    }
                )
                with patch('sys.stdout', stdout):
                    ENGINE.main(['draft-assessment'])

        result = json.loads(stdout.getvalue())
        self.assertEqual(result['assessment_template']['session_id'], 'sess-most-recent')

    def test_prepare_import_review_writes_seed_files(self):
        payload = {
            'session_id': 'sess-prep',
            'tool': 'codex',
            'transcript': [
                {'role': 'user', 'content': 'Audit the deploy rollback path.'},
                {'role': 'user', 'content': 'Keep the patch minimal and testable.'},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(payload)
                prepared = ENGINE.prepare_import_review(session_id='sess-prep')
                assessment_file = Path(prepared['assessment_file'])
                replay_file = Path(prepared['replay_file'])
                stored_assessment = json.loads(assessment_file.read_text(encoding='utf-8'))
                stored_replay = replay_file.read_text(encoding='utf-8')

        self.assertEqual(stored_assessment['session_id'], 'sess-prep')
        self.assertEqual(stored_assessment['meaningful_user_messages'], 2)
        self.assertIn('PromptIQ Session Replay', stored_replay)
        self.assertIn('score-import', prepared['next_command'])
        self.assertIn('--assessment-file', prepared['next_command'])
        self.assertIn('Edit the assessment_file in place', '\n'.join(prepared['notes']))

    def test_main_supports_prepare_import_review_without_session_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stdout = io.StringIO()

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(
                    {
                        'session_id': 'sess-prep-cli',
                        'transcript': [{'role': 'user', 'content': 'Prepare the latest imported review.'}],
                    }
                )
                with patch('sys.stdout', stdout):
                    ENGINE.main(['prepare-import-review'])

        result = json.loads(stdout.getvalue())
        self.assertEqual(result['source']['session_id'], 'sess-prep-cli')
        self.assertTrue(Path(result['assessment_file']).exists())
        self.assertTrue(Path(result['replay_file']).exists())

    def test_score_import_prepare_mode_returns_seed_workspace(self):
        payload = {
            'session_id': 'sess-score-import',
            'transcript': [{'role': 'user', 'content': 'Use score-import as the single command entrypoint.'}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(payload)
                result = ENGINE.score_import({}, save=False)

        self.assertEqual(result['mode'], 'prepare')
        self.assertEqual(result['source']['session_id'], 'sess-score-import')
        self.assertIn('score-import', result['next_command'])
        self.assertTrue(Path(result['assessment_file']).exists())

    def test_main_supports_score_import_prepare_without_session_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stdout = io.StringIO()

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(
                    {
                        'session_id': 'sess-score-import-cli',
                        'transcript': [{'role': 'user', 'content': 'Prepare score-import from the latest session.'}],
                    }
                )
                with patch('sys.stdout', stdout):
                    ENGINE.main(['score-import'])

        result = json.loads(stdout.getvalue())
        self.assertEqual(result['mode'], 'prepare')
        self.assertEqual(result['source']['session_id'], 'sess-score-import-cli')
        self.assertTrue(Path(result['assessment_file']).exists())

    def test_main_supports_score_import_finalize_with_assessment_file(self):
        payload = {
            'session_id': 'sess-score-finalize',
            'tool': 'codex',
            'transcript': [
                {'role': 'user', 'content': 'Audit the middleware regression.'},
                {'role': 'user', 'content': 'Keep the fix minimal and verify it.'},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stdout = io.StringIO()

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                ENGINE.import_session(payload)
                prepared = ENGINE.prepare_import_review(session_id='sess-score-finalize')
                assessment_path = Path(prepared['assessment_file'])
                completed_assessment = make_assessment(
                    session_id='sess-score-finalize',
                    session_fingerprint=prepared['source']['session_fingerprint'],
                    tool='codex',
                    session_summary='Imported middleware regression review',
                    meaningful_user_messages=2,
                    complexity='medium',
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
                        'verification_signals': 1,
                    },
                )
                assessment_path.write_text(json.dumps(completed_assessment), encoding='utf-8')
                with patch('sys.stdout', stdout):
                    ENGINE.main(['score-import', '--assessment-file', str(assessment_path), '--save'])

        result = json.loads(stdout.getvalue())
        self.assertEqual(result['mode'], 'finalized')
        self.assertEqual(result['history_write'], 'saved_new')
        self.assertEqual(result['session_record']['session_id'], 'sess-score-finalize')

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
            rubric_path = root / 'rubric_v1.json'
            history_file = root / 'history.json'

            helper.write_text('#!/usr/bin/env python3\n', encoding='utf-8')
            rubric_path.write_text(json.dumps(RUBRIC), encoding='utf-8')
            history_file.write_text(
                json.dumps({'sessions': [{'total': 7.0, 'rubric_version': RUBRIC['rubric_version']}]})
            )

            with patch.dict(ENGINE.os.environ, {'PROMPTIQ_HOME': str(root)}, clear=False):
                report = ENGINE.doctor(helper, rubric_path)

        self.assertEqual(report['status'], 'ok')
        self.assertEqual(report['history_session_count'], 1)
        self.assertEqual(report['rubric_version'], RUBRIC['rubric_version'])
        self.assertEqual(report['issues'], [])

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


if __name__ == '__main__':
    unittest.main()
