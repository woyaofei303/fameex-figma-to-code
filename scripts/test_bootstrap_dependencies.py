import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Dict, Optional
import unittest


SCRIPT = Path(__file__).with_name('bootstrap_dependencies.py')
EXPECTED_DEPENDENCIES = {
    'figma',
    'figma-implement-design',
    'playwright',
    'verification-before-completion',
}


def run_bootstrap(
    codex_home: Path,
    *args: str,
    env: Optional[Dict[str, str]] = None,
):
    command = [
        sys.executable,
        str(SCRIPT),
        '--codex-home',
        str(codex_home),
        *args,
    ]
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        env=process_env,
        text=True,
    )


def parse_result(result):
    return json.loads(result.stdout)


def read_skill_name(skill_md: Path):
    content = skill_md.read_text()
    match = re.search(r'^name:\s*([a-z0-9-]+)\s*$', content, re.MULTILINE)
    return match.group(1).strip() if match else None


class BootstrapDependenciesTest(unittest.TestCase):
    def test_creates_all_dependencies_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)

            first = run_bootstrap(codex_home, '--json')

            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
            first_payload = parse_result(first)
            self.assertEqual(
                {item['name'] for item in first_payload['results']},
                EXPECTED_DEPENDENCIES,
            )
            self.assertEqual(
                {item['status'] for item in first_payload['results']},
                {'created'},
            )
            for name in EXPECTED_DEPENDENCIES:
                skill_md = codex_home / 'skills' / name / 'SKILL.md'
                self.assertTrue(skill_md.is_file())
                self.assertEqual(read_skill_name(skill_md), name)

            second = run_bootstrap(codex_home, '--json')

            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            self.assertEqual(
                {item['status'] for item in parse_result(second)['results']},
                {'present'},
            )

    def test_bootstraps_only_requested_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)

            result = run_bootstrap(
                codex_home,
                '--dependency',
                'figma',
                '--json',
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = parse_result(result)
            self.assertEqual([item['name'] for item in payload['results']], ['figma'])
            self.assertEqual(payload['results'][0]['status'], 'created')
            self.assertEqual(
                {path.name for path in (codex_home / 'skills').iterdir()},
                {'figma'},
            )

    def test_preserves_invalid_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)
            invalid_skill = codex_home / 'skills' / 'figma' / 'SKILL.md'
            invalid_skill.parent.mkdir(parents=True)
            invalid_skill.write_text('invalid')

            result = run_bootstrap(
                codex_home,
                '--dependency',
                'figma',
                '--json',
            )

            self.assertEqual(result.returncode, 1)
            self.assertEqual(invalid_skill.read_text(), 'invalid')
            payload = parse_result(result)
            self.assertEqual(payload['results'][0]['status'], 'invalid')

    def test_reports_missing_npx_for_playwright(self):
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)

            result = run_bootstrap(
                codex_home,
                '--dependency',
                'playwright',
                '--json',
                env={'PATH': '/usr/bin:/bin'},
            )

            self.assertEqual(result.returncode, 1)
            payload = parse_result(result)
            self.assertEqual(payload['results'][0]['status'], 'created')
            self.assertEqual(
                payload['results'][0]['prerequisite'],
                'missing:npx',
            )


if __name__ == '__main__':
    unittest.main()
