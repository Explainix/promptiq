#!/usr/bin/env python3
"""Install PromptIQ helper files and available CLI integrations."""

from __future__ import annotations

import json
import shutil
import stat
import subprocess
from pathlib import Path
from urllib.request import urlopen

RAW_BASE = 'https://raw.githubusercontent.com/Explainix/promptiq/main'
REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER_LOCAL = REPO_ROOT / 'engine' / 'promptiq.py'
RUBRIC_LOCAL = REPO_ROOT / 'engine' / 'rubric_v1.json'

SKILL_BUNDLES = {
    'promptiq': [
        (
            REPO_ROOT / 'skills' / 'score' / 'SKILL.md',
            'skills/score/SKILL.md',
            'SKILL.md',
        ),
        (
            REPO_ROOT / 'skills' / 'score' / 'references' / 'assessment-schema.md',
            'skills/score/references/assessment-schema.md',
            'references/assessment-schema.md',
        ),
        (
            REPO_ROOT / 'skills' / 'score' / 'references' / 'report-template.md',
            'skills/score/references/report-template.md',
            'references/report-template.md',
        ),
    ],
    'promptiq-install': [
        (
            REPO_ROOT / 'skills' / 'install' / 'SKILL.md',
            'skills/install/SKILL.md',
            'SKILL.md',
        ),
        (
            REPO_ROOT / 'skills' / 'install' / 'scripts' / 'install_promptiq.py',
            'skills/install/scripts/install_promptiq.py',
            'scripts/install_promptiq.py',
        ),
    ],
}


def write_text(dest: Path, text: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)


def fetch_text(url: str) -> str:
    with urlopen(url) as response:
        return response.read().decode('utf-8')


def install_file(dest: Path, local_path: Path, remote_path: str) -> str:
    if local_path.exists():
        write_text(dest, local_path.read_text())
        return 'local'
    write_text(dest, fetch_text(f'{RAW_BASE}/{remote_path}'))
    return 'remote'


def install_bundle(dest_root: Path, files: list[tuple[Path, str, str]]) -> str:
    sources: set[str] = set()
    for local_path, remote_path, relative_dest in files:
        source = install_file(dest_root / relative_dest, local_path, remote_path)
        sources.add(source)
    return '+'.join(sorted(sources))


def mark_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR)


def run_command(args: list[str]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return False, 'not_found'
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode == 0:
        return True, output or 'ok'
    lowered = output.lower()
    if 'already' in lowered and ('installed' in lowered or 'exists' in lowered):
        return True, output
    return False, output or 'failed'


def install_claude_plugin() -> str:
    if shutil.which('claude') is None:
        return 'not_found'

    add_ok, add_output = run_command(['claude', 'plugin', 'marketplace', 'add', 'Explainix/promptiq'])
    install_ok, install_output = run_command(['claude', 'plugin', 'install', 'promptiq'])

    if add_ok and install_ok:
        return 'installed'
    if 'already' in add_output.lower() or 'already' in install_output.lower():
        return 'already_installed'
    return f'install_failed: {install_output}'


def install_codex_skill() -> str:
    if shutil.which('codex') is None:
        return 'not_found'

    skills_root = Path.home() / '.codex' / 'skills'
    installed: dict[str, str] = {}

    for skill_name, files in SKILL_BUNDLES.items():
        installed[skill_name] = install_bundle(skills_root / skill_name, files)

    return f"installed {json.dumps(installed, sort_keys=True)}"


def main() -> int:
    if shutil.which('python3') is None:
        print('PromptIQ installation failed: python3 is required.')
        return 1

    helper_dir = Path.home() / '.promptiq'
    helper_source = install_file(helper_dir / 'promptiq.py', HELPER_LOCAL, 'engine/promptiq.py')
    rubric_source = install_file(helper_dir / 'rubric_v1.json', RUBRIC_LOCAL, 'engine/rubric_v1.json')
    mark_executable(helper_dir / 'promptiq.py')

    codex_status = install_codex_skill()
    claude_status = install_claude_plugin()

    print('PromptIQ installed successfully.')
    print()
    print('  Trigger:   /score')
    print(f'  Helper:    {helper_dir / "promptiq.py"} ({helper_source})')
    print(f'  Rubric:    {helper_dir / "rubric_v1.json"} ({rubric_source})')
    print(f'  History:   {helper_dir / "history.json"}')
    print('  Python 3:  found')
    print(f'  Codex:     {codex_status}')
    print(f'  Claude:    {claude_status}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
