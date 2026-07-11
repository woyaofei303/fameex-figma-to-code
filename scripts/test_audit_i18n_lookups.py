import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('audit_i18n_lookups.py')


def run_audit(
    namespace_json: Path,
    *sources: Path,
    keys=(),
    as_json: bool = True,
):
    command = [
        sys.executable,
        str(SCRIPT),
        '--namespace-json',
        str(namespace_json),
    ]
    for source in sources:
        command.extend(('--source', str(source)))
    for key in keys:
        command.extend(('--key', key))
    if as_json:
        command.append('--json')
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
    )


class AuditI18nLookupsTest(unittest.TestCase):
    def write_namespace(self, root: Path, payload) -> Path:
        path = root / 'zh-CN' / 'namespace.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(payload), encoding='utf-8')
        return path

    def test_exact_literal_lookups_match_nested_object_and_array_leaves(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(
                root,
                {
                    'page': {
                        'title': 'Title',
                        'steps': ['first', 'second'],
                    }
                },
            )
            source = root / 'page.tsx'
            source.write_text(
                "const title = t('page.title')\nconst steps = t('page.steps')\n",
                encoding='utf-8',
            )

            result = run_audit(namespace, source)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                json.loads(result.stdout),
                {
                    'referenced_count': 2,
                    'leaf_count': 2,
                    'missing_keys': [],
                    'unused_keys': [],
                },
            )

    def test_detects_single_and_double_quoted_first_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(
                root,
                {'single': 'Single', 'double': 'Double'},
            )
            source = root / 'quotes.ts'
            source.write_text(
                "t('single');\nt(\"double\", { count: 1 });\n",
                encoding='utf-8',
            )

            result = run_audit(namespace, source)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)['referenced_count'], 2)

    def test_detects_literal_branches_of_simple_conditional_first_argument(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(
                root,
                {'enabled': 'Enabled', 'disabled': 'Disabled'},
            )
            source = root / 'conditional.jsx'
            source.write_text(
                "t(isEnabled ? 'enabled' : \"disabled\")\n",
                encoding='utf-8',
            )

            result = run_audit(namespace, source)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)['referenced_count'], 2)

    def test_explicit_keys_supply_computed_and_template_expansions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(
                root,
                {'status': {'active': 'Active', 'paused': 'Paused'}},
            )
            source = root / 'dynamic.tsx'
            source.write_text(
                "t(`status.${status}`);\nt(statusKey);\n",
                encoding='utf-8',
            )

            result = run_audit(
                namespace,
                source,
                keys=('status.paused', 'status.active'),
            )

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)['referenced_count'], 2)

    def test_ignores_ghost_calls_outside_global_normal_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(root, {'real': 'Real'})
            source = root / 'lexical.tsx'
            source.write_text(
                '''const single = "t('inside-double-string')"
const double = 't("inside-single-string")'
const template = `t('inside-template')`
// t('inside-line-comment')
/* t('inside-block-comment') */
object.t('member-call')
object?.t('optional-member-call')
$t('dollar-prefixed-call')
t('real')
''',
                encoding='utf-8',
            )

            result = run_audit(namespace, source)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)['referenced_count'], 1)

    def test_decodes_javascript_unicode_code_point_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(root, {'a': 'A'})
            source = root / 'unicode.ts'
            source.write_text("t('\\u{0061}')\n", encoding='utf-8')

            result = run_audit(namespace, source)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)['referenced_count'], 1)

    def test_invalid_javascript_escape_exits_two_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(root, {'unused': 'Unused'})
            source = root / 'invalid.ts'
            source.write_text("t('\\xG1')\n", encoding='utf-8')

            result = run_audit(namespace, source)

            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertIn('invalid JavaScript string literal', result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_directory_sources_recurse_supported_extensions_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(
                root,
                {'js': 'JS', 'jsx': 'JSX', 'ts': 'TS', 'tsx': 'TSX'},
            )
            source_dir = root / 'feature'
            nested = source_dir / 'nested'
            nested.mkdir(parents=True)
            (source_dir / 'a.js').write_text("t('js')\n", encoding='utf-8')
            (source_dir / 'b.jsx').write_text("t('jsx')\n", encoding='utf-8')
            (nested / 'c.ts').write_text("t('ts')\n", encoding='utf-8')
            (nested / 'd.tsx').write_text("t('tsx')\n", encoding='utf-8')
            (nested / 'ignored.vue').write_text(
                "t('not-a-leaf')\n",
                encoding='utf-8',
            )

            result = run_audit(namespace, source_dir)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)['referenced_count'], 4)

    def test_repeatable_file_sources_all_contribute_lookups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(
                root,
                {'first': 'First', 'second': 'Second'},
            )
            first = root / 'first.ts'
            first.write_text("t('first')\n", encoding='utf-8')
            second = root / 'second.tsx'
            second.write_text("t('second')\n", encoding='utf-8')

            result = run_audit(namespace, first, second)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)['referenced_count'], 2)

    def test_mismatch_json_is_sorted_deterministically_and_exits_one(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(
                root,
                {'used': 'Used', 'z_unused': 'Z', 'a_unused': 'A'},
            )
            source = root / 'page.tsx'
            source.write_text(
                "t('z_missing'); t('used'); t('a_missing');\n",
                encoding='utf-8',
            )

            result = run_audit(namespace, source)

            self.assertEqual(result.returncode, 1, result.stderr or result.stdout)
            self.assertEqual(
                json.loads(result.stdout),
                {
                    'referenced_count': 3,
                    'leaf_count': 3,
                    'missing_keys': ['a_missing', 'z_missing'],
                    'unused_keys': ['a_unused', 'z_unused'],
                },
            )

    def test_plain_output_is_concise_and_line_addressable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = self.write_namespace(root, {'unused': 'Unused'})
            source = root / 'page.tsx'
            source.write_text("t('missing')\n", encoding='utf-8')

            result = run_audit(namespace, source, as_json=False)

            self.assertEqual(result.returncode, 1, result.stderr or result.stdout)
            self.assertEqual(
                result.stdout.splitlines(),
                [
                    'i18n lookup audit: referenced=1 leaves=1 missing=1 unused=1',
                    'missing:missing',
                    'unused:unused',
                ],
            )

    def test_invalid_inputs_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid_namespace = self.write_namespace(root, {'key': 'Value'})
            valid_source = root / 'page.tsx'
            valid_source.write_text("t('key')\n", encoding='utf-8')

            missing_namespace = run_audit(root / 'missing.json', valid_source)
            self.assertEqual(missing_namespace.returncode, 2)
            self.assertIn('namespace JSON', missing_namespace.stderr)

            malformed = root / 'malformed.json'
            malformed.write_text('{malformed', encoding='utf-8')
            malformed_result = run_audit(malformed, valid_source)
            self.assertEqual(malformed_result.returncode, 2)
            self.assertIn('invalid JSON', malformed_result.stderr)

            array_root = root / 'array.json'
            array_root.write_text('[]', encoding='utf-8')
            array_result = run_audit(array_root, valid_source)
            self.assertEqual(array_result.returncode, 2)
            self.assertIn('JSON object', array_result.stderr)

            missing_source = run_audit(valid_namespace, root / 'missing.tsx')
            self.assertEqual(missing_source.returncode, 2)
            self.assertIn('source path does not exist', missing_source.stderr)

            unsupported = root / 'ignored.vue'
            unsupported.write_text("t('key')\n", encoding='utf-8')
            unsupported_result = run_audit(valid_namespace, unsupported)
            self.assertEqual(unsupported_result.returncode, 2)
            self.assertIn('no supported source files', unsupported_result.stderr)


if __name__ == '__main__':
    unittest.main()
