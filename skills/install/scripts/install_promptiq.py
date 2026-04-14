#!/usr/bin/env python3
"""Install PromptIQ helper files and available CLI integrations."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
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
    'promptiq-score-import': [
        (
            REPO_ROOT / 'skills' / 'score-import' / 'SKILL.md',
            'skills/score-import/SKILL.md',
            'SKILL.md',
        ),
        (
            REPO_ROOT / 'skills' / 'score-import' / 'references' / 'output-template.md',
            'skills/score-import/references/output-template.md',
            'references/output-template.md',
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
    'promptiq-rewrite-last': [
        (
            REPO_ROOT / 'skills' / 'rewrite-last' / 'SKILL.md',
            'skills/rewrite-last/SKILL.md',
            'SKILL.md',
        ),
        (
            REPO_ROOT / 'skills' / 'rewrite-last' / 'references' / 'output-template.md',
            'skills/rewrite-last/references/output-template.md',
            'references/output-template.md',
        ),
    ],
}


def write_text(dest: Path, text: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding='utf-8')


def fetch_text(url: str) -> str:
    with urlopen(url, timeout=20) as response:
        return response.read().decode('utf-8')


def env_flag(name: str) -> bool:
    return os.environ.get(name, '').strip().lower() in {'1', 'true', 'yes', 'on'}


def resolve_promptiq_home(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    override = os.environ.get('PROMPTIQ_HOME')
    if override:
        return Path(override).expanduser()
    return Path.home() / '.promptiq'


def resolve_codex_home(explicit: str | None = None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser()
    override = os.environ.get('CODEX_HOME')
    if override:
        return Path(override).expanduser()
    default_home = Path.home() / '.codex'
    if shutil.which('codex') is not None or default_home.exists():
        return default_home
    return None


def install_file(dest: Path, local_path: Path, remote_path: str) -> str:
    if local_path.exists():
        write_text(dest, local_path.read_text(encoding='utf-8'))
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


def install_claude_plugin(skip: bool = False) -> str:
    if skip:
        return 'skipped'
    if shutil.which('claude') is None:
        return 'not_found'

    add_ok, add_output = run_command(['claude', 'plugin', 'marketplace', 'add', 'Explainix/promptiq'])
    install_ok, install_output = run_command(['claude', 'plugin', 'install', 'promptiq'])

    if add_ok and install_ok:
        return 'installed'
    if 'already' in add_output.lower() or 'already' in install_output.lower():
        return 'already_installed'
    return f'install_failed: {install_output}'


def install_codex_skill(codex_home: Path | None = None, skip: bool = False) -> str:
    if skip:
        return 'skipped'

    resolved_codex_home = codex_home or resolve_codex_home()
    if resolved_codex_home is None:
        return 'not_found'

    skills_root = resolved_codex_home / 'skills'
    installed: dict[str, str] = {}

    for skill_name, files in SKILL_BUNDLES.items():
        installed[skill_name] = install_bundle(skills_root / skill_name, files)

    return f"installed {json.dumps(installed, sort_keys=True)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Install PromptIQ helper files and optional CLI integrations.')
    parser.add_argument('--promptiq-home', help='Install helper files into this directory instead of ~/.promptiq.')
    parser.add_argument('--codex-home', help='Install Codex skills into this directory instead of ~/.codex.')
    parser.add_argument('--skip-codex', action='store_true', help='Skip installing the Codex skill bundles.')
    parser.add_argument('--skip-claude', action='store_true', help='Skip installing the Claude plugin.')
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    if shutil.which('python3') is None:
        print('PromptIQ installation failed: python3 is required.')
        return 1

    helper_dir = resolve_promptiq_home(args.promptiq_home)
    codex_home = resolve_codex_home(args.codex_home)
    skip_codex = args.skip_codex or env_flag('PROMPTIQ_SKIP_CODEX')
    skip_claude = args.skip_claude or env_flag('PROMPTIQ_SKIP_CLAUDE')

    try:
        helper_source = install_file(helper_dir / 'promptiq.py', HELPER_LOCAL, 'engine/promptiq.py')
        rubric_source = install_file(helper_dir / 'rubric_v1.json', RUBRIC_LOCAL, 'engine/rubric_v1.json')
        mark_executable(helper_dir / 'promptiq.py')
        codex_status = install_codex_skill(codex_home=codex_home, skip=skip_codex)
        claude_status = install_claude_plugin(skip=skip_claude)
    except PermissionError as exc:
        print(f'PromptIQ installation failed: permission denied while writing to {exc.filename or exc}.')
        print('Hint: set PROMPTIQ_HOME and optionally CODEX_HOME to a writable location, or rerun with appropriate permissions.')
        return 1
    except OSError as exc:
        print(f'PromptIQ installation failed: {exc}')
        return 1

    print('PromptIQ installed successfully.')
    print()
    print('  Trigger:   /score')
    print(f'  Config:    PROMPTIQ_HOME={helper_dir}')
    print(f'  Helper:    {helper_dir / "promptiq.py"} ({helper_source})')
    print(f'  Rubric:    {helper_dir / "rubric_v1.json"} ({rubric_source})')
    print(f'  History:   {helper_dir / "history.json"}')
    print(f'  Imports:   {helper_dir / "imports"}')
    print(f'  Verify:    python3 "{helper_dir / "promptiq.py"}" doctor')
    print('  Python 3:  found')
    print(f'  Codex:     {codex_status}')
    print(f'  Claude:    {claude_status}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
