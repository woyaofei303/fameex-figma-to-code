import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('audit_reuse.py')


def run_audit(repo_root: Path, *targets: Path, as_json: bool = True):
    command = [
        sys.executable,
        str(SCRIPT),
        '--repo-root',
        str(repo_root),
        *(str(target) for target in targets),
    ]
    if as_json:
        command.append('--json')
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
    )


class AuditReuseTest(unittest.TestCase):
    def test_does_not_attribute_an_unsupported_import_to_the_next_library(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/page.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                """import { type ReactNode, useState } from 'react'
import { Button, Input } from '@fameex/ui'
""",
            )

            result = run_audit(repo_root, fixture)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                json.loads(result.stdout)['libraries'],
                {'@fameex/ui': ['Button', 'Input']},
            )

    def test_reports_reuse_signals_for_a_directory_target(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            icon_list = repo_root / 'packages/icon/output/icon-list.json'
            icon_list.parent.mkdir(parents=True)
            icon_list.write_text(
                json.dumps(['icon-[fx--search]', 'icon-[fx--close]']),
            )
            fixture = repo_root / 'apps/console/src/features/SearchPanel.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                """import { Button, Input as FameInput } from '@fameex/ui';
import { Select } from 'antd';

export function SearchPanel() {
  return (
    <section>
      <Button />
      <FameInput />
      <Select />
      <button type="button" className="icon-[fx--search]">Search</button>
      <input className="icon-[fx--missing]" />
      <img src="/search.png" alt="Search" />
    </section>
  );
}
""",
            )

            result = run_audit(repo_root, repo_root / 'apps/console')

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                json.loads(result.stdout),
                {
                    'libraries': {
                        '@fameex/ui': ['Button', 'Input'],
                        'antd': ['Select'],
                    },
                    'native_controls': {
                        'button': 1,
                        'input': 1,
                        'select': 0,
                        'textarea': 0,
                    },
                    'images': 1,
                    'icons': [
                        {'class': 'icon-[fx--search]', 'available': True},
                        {'class': 'icon-[fx--missing]', 'available': False},
                    ],
                },
            )

    def test_accepts_multiple_file_targets_and_prints_a_plain_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            first = repo_root / 'modules/first.tsx'
            second = repo_root / 'other/second.vue'
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_text("import { Card } from '@heroui/react';\n<button />\n")
            second.write_text("import { ElInput } from 'element-plus';\n<img />\n")

            result = run_audit(repo_root, first, second, as_json=False)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn('@heroui/react: Card', result.stdout)
            self.assertIn('element-plus: ElInput', result.stdout)
            self.assertIn(
                'Native controls: button=1, input=0, select=0, textarea=0',
                result.stdout,
            )
            self.assertIn('Images: 1', result.stdout)


if __name__ == '__main__':
    unittest.main()
