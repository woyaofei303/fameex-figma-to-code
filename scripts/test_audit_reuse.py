import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('audit_reuse.py')


def run_audit(
    repo_root: Path,
    *targets: Path,
    as_json: bool = True,
    limit: int = 100,
):
    command = [
        sys.executable,
        str(SCRIPT),
        '--repo-root',
        str(repo_root),
        '--limit',
        str(limit),
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
    def test_unavailable_icon_catalog_omits_availability(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/icon.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text('<i className="icon-[fx--search]" />\n')

            missing_result = run_audit(repo_root, fixture)

            self.assertEqual(
                missing_result.returncode,
                0,
                missing_result.stderr or missing_result.stdout,
            )
            missing_icon = json.loads(missing_result.stdout)['candidates'][0]
            self.assertNotIn('available', missing_icon)

            icon_list = repo_root / 'packages/icon/output/icon-list.json'
            icon_list.parent.mkdir(parents=True)
            icon_list.write_text('{malformed')

            malformed_result = run_audit(repo_root, fixture)

            self.assertEqual(
                malformed_result.returncode,
                0,
                malformed_result.stderr or malformed_result.stdout,
            )
            malformed_icon = json.loads(malformed_result.stdout)['candidates'][0]
            self.assertNotIn('available', malformed_icon)

    def test_rejects_repo_root_that_is_not_an_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            fixture = parent / 'page.tsx'
            fixture.write_text('<button />\n')
            missing_repo = parent / 'missing-repo'

            result = run_audit(missing_repo, fixture)

            self.assertEqual(result.returncode, 2)
            self.assertIn('repo root is not an existing directory', result.stderr)

    def test_long_line_excerpt_is_centered_on_the_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/long-line.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                'const padding = "{}"; const fixture = \'{}icon-[fx--search]\'\n'.format(
                    'x' * 280,
                    'nearby-' * 3,
                ),
            )

            result = run_audit(repo_root, fixture)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            source = json.loads(result.stdout)['candidates'][0]['source']
            self.assertIn('icon-[fx--search]', source)
            self.assertIn("const fixture = '", source)
            self.assertTrue(source.startswith('...'))
            self.assertLessEqual(len(source), 240)

    def test_multiline_component_import_points_to_package_literal_line(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/multiline.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                """import { Button }
from
'@fameex/ui'
""",
            )

            result = run_audit(repo_root, fixture)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                json.loads(result.stdout)['candidates'],
                [
                    {
                        'kind': 'component-import',
                        'name': '@fameex/ui',
                        'file': 'src/multiline.tsx',
                        'line': 3,
                        'source': "'@fameex/ui'",
                    }
                ],
            )

    def test_file_target_reports_line_candidates_and_icon_availability(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            icon_list = repo_root / 'packages/icon/output/icon-list.json'
            icon_list.parent.mkdir(parents=True)
            icon_list.write_text(json.dumps(['icon-[fx--search]']))
            fixture = repo_root / 'src/page.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                """import { Button } from '@fameex/ui'
const searchIcon = 'icon-[fx--search]'
// <button className="icon-[fx--missing]" />
<img alt="" />
""",
            )

            result = run_audit(repo_root, fixture)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                json.loads(result.stdout),
                {
                    'candidates': [
                        {
                            'kind': 'component-import',
                            'name': '@fameex/ui',
                            'file': 'src/page.tsx',
                            'line': 1,
                            'source': "import { Button } from '@fameex/ui'",
                        },
                        {
                            'kind': 'icon-literal',
                            'name': 'icon-[fx--search]',
                            'file': 'src/page.tsx',
                            'line': 2,
                            'source': "const searchIcon = 'icon-[fx--search]'",
                            'available': True,
                        },
                        {
                            'kind': 'native-control',
                            'name': 'button',
                            'file': 'src/page.tsx',
                            'line': 3,
                            'source': '// <button className="icon-[fx--missing]" />',
                        },
                        {
                            'kind': 'icon-literal',
                            'name': 'icon-[fx--missing]',
                            'file': 'src/page.tsx',
                            'line': 3,
                            'source': '// <button className="icon-[fx--missing]" />',
                            'available': False,
                        },
                        {
                            'kind': 'image',
                            'name': 'img',
                            'file': 'src/page.tsx',
                            'line': 4,
                            'source': '<img alt="" />',
                        },
                    ],
                    'limit': 100,
                    'total': 5,
                    'omitted': 0,
                },
            )

    def test_directory_target_recurses_supported_source_extensions(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            target = repo_root / 'arbitrary-area'
            nested = target / 'nested'
            nested.mkdir(parents=True)
            (target / 'first.js').write_text(
                "import { Select } from 'antd'\n<select />\n",
            )
            (nested / 'second.vue').write_text('<input />\n<textarea />\n')
            (nested / 'ignored.txt').write_text('<button />\n')

            result = run_audit(repo_root, target)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(
                [
                    (item['file'], item['line'], item['kind'], item['name'])
                    for item in payload['candidates']
                ],
                [
                    ('arbitrary-area/first.js', 1, 'component-import', 'antd'),
                    ('arbitrary-area/first.js', 2, 'native-control', 'select'),
                    (
                        'arbitrary-area/nested/second.vue',
                        1,
                        'native-control',
                        'input',
                    ),
                    (
                        'arbitrary-area/nested/second.vue',
                        2,
                        'native-control',
                        'textarea',
                    ),
                ],
            )
            self.assertEqual(payload['total'], 4)
            self.assertEqual(payload['omitted'], 0)

    def test_limit_bounds_json_candidates_and_reports_omitted_count(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/limited.jsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                """<button />
<input />
<img />
<i className="icon-[fx--search]" />
""",
            )

            result = run_audit(repo_root, fixture, limit=2)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload['candidates']), 2)
            self.assertEqual(payload['limit'], 2)
            self.assertEqual(payload['total'], 4)
            self.assertEqual(payload['omitted'], 2)

    def test_plain_output_labels_candidates_and_manual_judgement(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / 'src/plain.tsx'
            fixture.parent.mkdir(parents=True)
            fixture.write_text('<button />\n<img />\n')

            result = run_audit(
                repo_root,
                fixture,
                as_json=False,
                limit=1,
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn('Reuse audit candidates', result.stdout)
            self.assertIn('src/plain.tsx:1 [native-control] button', result.stdout)
            self.assertIn('omitted 1', result.stdout)
            self.assertIn('Candidates only; agent judgement required', result.stdout)


if __name__ == '__main__':
    unittest.main()
