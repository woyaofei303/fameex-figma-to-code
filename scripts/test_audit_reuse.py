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
    def test_ignores_line_block_and_jsx_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/commented.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                """import { Button } from '@fameex/ui'
// import { Select } from 'antd'
// <input className="icon-[fx--comment-line]" /><img />
/*
import { Input } from '@fameex/ui'
<select className="icon-[fx--comment-block]" /><img />
*/

export function Commented() {
  return (
    <div>
      {/* <textarea className="icon-[fx--comment-jsx]" /><img /> */}
      <button className="icon-[fx--search]" />
      <img />
    </div>
  )
}
""",
            )

            result = run_audit(repo_root, fixture)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                json.loads(result.stdout),
                {
                    'libraries': {'@fameex/ui': ['Button']},
                    'native_controls': {
                        'button': 1,
                        'input': 0,
                        'select': 0,
                        'textarea': 0,
                    },
                    'images': 1,
                    'icons': [
                        {'class': 'icon-[fx--search]', 'available': False},
                    ],
                },
            )

    def test_ignores_string_and_template_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/fixtures.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                """import { Card } from '@heroui/react'
const singleFixture = '<input className="icon-[fx--single]" /><img />'
const doubleFixture = "import { Input } from '@fameex/ui'; <button />"
const templateFixture = `
  import { Select } from 'antd'
  <select className="icon-[fx--template]" />
  <textarea />
  <img />
`

export function Fixtures() {
  return (
    <div className="icon-[fx--search]">
      <textarea />
      <img />
    </div>
  )
}
""",
            )

            result = run_audit(repo_root, fixture)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                json.loads(result.stdout),
                {
                    'libraries': {'@heroui/react': ['Card']},
                    'native_controls': {
                        'button': 0,
                        'input': 0,
                        'select': 0,
                        'textarea': 1,
                    },
                    'images': 1,
                    'icons': [
                        {'class': 'icon-[fx--search]', 'available': False},
                    ],
                },
            )

    def test_ignores_standalone_type_only_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/types.ts'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                "import type { ButtonProps, InputProps } from '@fameex/ui'\n",
            )

            result = run_audit(repo_root, fixture)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)['libraries'], {})

    def test_keeps_runtime_components_from_mixed_type_and_value_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/components.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                """import {
  Button,
  type ButtonProps,
  Input as FameInput,
  type InputProps as FameInputProps,
} from '@fameex/ui'
""",
            )

            result = run_audit(repo_root, fixture)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                json.loads(result.stdout)['libraries'],
                {'@fameex/ui': ['Button', 'Input']},
            )

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
