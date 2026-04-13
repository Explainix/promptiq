import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = ROOT / 'skills' / 'install' / 'scripts' / 'install_promptiq.py'


def load_installer():
    spec = importlib.util.spec_from_file_location('promptiq_installer', INSTALLER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


INSTALLER = load_installer()


class PromptIQInstallerTests(unittest.TestCase):
    def test_install_codex_skill_bundle_copies_references(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            with patch.object(INSTALLER.Path, 'home', return_value=home):
                with patch.object(INSTALLER.shutil, 'which', side_effect=lambda name: '/usr/bin/codex' if name == 'codex' else None):
                    status = INSTALLER.install_codex_skill()

            self.assertIn('installed', status)
            self.assertTrue((home / '.codex' / 'skills' / 'promptiq' / 'SKILL.md').exists())
            self.assertTrue((home / '.codex' / 'skills' / 'promptiq' / 'references' / 'assessment-schema.md').exists())
            self.assertTrue((home / '.codex' / 'skills' / 'promptiq' / 'references' / 'report-template.md').exists())
            self.assertTrue((home / '.codex' / 'skills' / 'promptiq-install' / 'SKILL.md').exists())
            self.assertTrue((home / '.codex' / 'skills' / 'promptiq-install' / 'scripts' / 'install_promptiq.py').exists())

    def test_install_codex_skill_reports_not_found_without_codex(self):
        with patch.object(INSTALLER.shutil, 'which', return_value=None):
            self.assertEqual(INSTALLER.install_codex_skill(), 'not_found')

    def test_main_installs_helper_and_codex_bundle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)

            def fake_which(name: str):
                if name == 'python3':
                    return '/usr/bin/python3'
                if name == 'codex':
                    return '/usr/bin/codex'
                return None

            with patch.object(INSTALLER.Path, 'home', return_value=home):
                with patch.object(INSTALLER.shutil, 'which', side_effect=fake_which):
                    with patch.object(INSTALLER, 'install_claude_plugin', return_value='not_found'):
                        code = INSTALLER.main()

            self.assertEqual(code, 0)
            self.assertTrue((home / '.promptiq' / 'promptiq.py').exists())
            self.assertTrue((home / '.promptiq' / 'rubric_v1.json').exists())


if __name__ == '__main__':
    unittest.main()
