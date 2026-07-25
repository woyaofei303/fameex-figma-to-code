import base64
import binascii
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/validate_visual_evidence.py'
COMPARE_SCRIPT = ROOT / 'scripts/compare_assets_rgba.py'
TEMPLATE = ROOT / 'assets/templates/visual-evidence.json'


def png_chunk(kind, payload):
    return (
        struct.pack('>I', len(payload))
        + kind
        + payload
        + struct.pack('>I', binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_rgba_png(path, rgba):
    path.write_bytes(
        b'\x89PNG\r\n\x1a\n'
        + png_chunk(
            b'IHDR',
            struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0),
        )
        + png_chunk(b'IDAT', zlib.compress(b'\x00' + bytes(rgba)))
        + png_chunk(b'IEND', b'')
    )


def observer_evidence(
    *,
    threshold=0.5,
    reentry_policy='once',
    disconnect_verified=True,
):
    return {
        'scroll_root': 'document',
        'overflow_owner': 'window',
        'root': 'viewport',
        'root_margin': '0px',
        'threshold': threshold,
        'initially_visible': True,
        'downward_entry_verified': True,
        'upward_entry_verified': True,
        'exit_verified': True,
        'reentry_policy': reentry_policy,
        'reentry_verified': True,
        'responsive_root_change_verified': True,
        'opacity_transform_verified': True,
        'unobserve_verified': True,
        'disconnect_verified': disconnect_verified,
        'reduced_motion_verified': True,
        'unsupported_observer_verified': True,
    }


class VisualEvidenceValidatorTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.repo = Path(self.temp_dir.name) / 'repo'
        self.audit_dir = (
            self.repo / 'output-tdd/figma-audits/PR-02107'
        )
        self.audit_dir.mkdir(parents=True)
        self.artifacts = {}
        json_payloads = {
            'context.json': {
                'source': 'figma-mcp',
                'status': 'passed',
                'file_key': 'KzvWxAYxqfgpoiYuKdxMAE',
                'node_id': '15863:18454',
            },
            'geometry.json': {
                'source': 'playwright',
                'status': 'passed',
                'section_ids': ['ranking', 'lottery'],
                'measurements': [
                    {
                        'target': 'ranking-grid',
                        'rect': {
                            'x': 100,
                            'y': 200,
                            'width': 320,
                            'height': 240,
                        },
                    },
                ],
            },
            'styles.json': {
                'source': 'playwright',
                'status': 'passed',
                'section_ids': ['ranking', 'lottery'],
                'computed_styles': [
                    {
                        'target': 'ranking-grid',
                        'display': 'grid',
                        'column_gap': 0,
                    },
                ],
            },
            'layers.json': {
                'source': 'playwright',
                'status': 'passed',
                'layer_ids': ['rank-gradient'],
            },
            'table.json': {
                'source': 'playwright',
                'status': 'passed',
                'section_id': 'ranking',
                'metrics': {
                    'first_column_edge': 16,
                    'last_column_edge': 16,
                    'scroll_width': 320,
                    'client_width': 320,
                },
                'columns': [
                    {
                        'id': 'uid',
                        'th': {
                            'start': 100,
                            'width': 120,
                            'center': 160,
                        },
                        'td': [
                            {
                                'row': 'first',
                                'start': 100,
                                'width': 120,
                                'center': 160,
                            },
                            {
                                'row': 'last',
                                'start': 100,
                                'width': 120,
                                'center': 160,
                            },
                            {
                                'row': 'content-extreme',
                                'start': 100,
                                'width': 120,
                                'center': 160,
                            },
                        ],
                    },
                ],
            },
            'motion.json': {
                'source': 'playwright',
                'status': 'passed',
                'section_id': 'lottery',
                'kind': 'interaction',
                'checks': {
                    'trigger': True,
                    'order': True,
                    'input_lock': True,
                    'completion': True,
                    'unmount': True,
                },
            },
        }
        for name in (
            'context.json',
            'screenshot.png',
            'geometry.json',
            'styles.json',
            'crop.png',
            'difference.png',
            'layers.json',
            'interaction.json',
            'table.json',
            'motion.json',
            'correction.png',
            'asset-difference.json',
        ):
            path = self.audit_dir / name
            if path.suffix == '.json':
                path.write_text(json.dumps(json_payloads.get(name, {})))
            else:
                write_rgba_png(path, (32, 64, 96, 255))
            self.artifacts[name] = str(path.relative_to(self.repo))
        (self.audit_dir / 'interaction.json').write_text(
            json.dumps(
                {
                    'source': 'playwright',
                    'status': 'passed',
                    'viewport': {'width': 320, 'height': 568},
                    'steps': {
                        'trigger': True,
                        'scroll_owner': True,
                        'close_control': True,
                        'final_action': True,
                        'safe_area': True,
                        'horizontal_scroll': 'not-applicable',
                    },
                }
            )
        )
        asset_dir = self.repo / 'assets'
        asset_dir.mkdir()
        self.source_asset = asset_dir / 'hero.png'
        write_rgba_png(self.source_asset, (234, 234, 234, 255))
        self.candidate_asset = asset_dir / 'hero.webp'
        self.candidate_asset.write_bytes(
            base64.b64decode(
                'UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEAAUAm'
                'JaQAA3AA/vuUAAA='
            )
        )
        self.source_sha256 = hashlib.sha256(
            self.source_asset.read_bytes()
        ).hexdigest()
        self.candidate_sha256 = hashlib.sha256(
            self.candidate_asset.read_bytes()
        ).hexdigest()
        subprocess.run(
            [
                '/usr/bin/python3',
                str(COMPARE_SCRIPT),
                '--source',
                str(self.source_asset),
                '--candidate',
                str(self.candidate_asset),
                '--output',
                str(self.audit_dir / 'asset-difference.json'),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        app_dir = self.repo / 'apps/web'
        app_dir.mkdir(parents=True)
        self.target_file = app_dir / 'page.tsx'
        self.target_file.write_text('export default function Page() {}')
        (self.repo / '.gitignore').write_text('output-tdd/\n')
        subprocess.run(
            ['git', 'init', '-q'],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ['git', 'config', 'user.email', 'tests@example.com'],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'Visual Evidence Tests'],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ['git', 'add', '.'],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ['git', 'commit', '-qm', 'test fixture'],
            cwd=self.repo,
            check=True,
        )

    def valid_manifest(self):
        return {
            'schema_version': '2.0',
            'task': {
                'id': 'PR-02107',
                'repository': str(self.repo),
                'mode': 'feature-delivery',
                'route': '/contract-carnival',
                'branch': 'feature/PR-02107',
                'locale': 'zh-CN',
                'target_paths': [
                    'apps/web/page.tsx',
                    'assets/hero.png',
                    'assets/hero.webp',
                ],
            },
            'claim': {
                'status': 'verified',
                'level': 'presentation-slice-verified',
            },
            'required_viewports': [
                {
                    'id': 'h5-short-required',
                    'kind': 'h5',
                    'width': 320,
                    'height': 568,
                    'full_interaction': True,
                    'source': 'user-feedback:share-modal',
                },
            ],
            'frames': [
                {
                    'id': 'desktop-default',
                    'file_key': 'KzvWxAYxqfgpoiYuKdxMAE',
                    'node_id': '15863:18454',
                    'state': 'default',
                    'viewport': {
                        'kind': 'desktop',
                        'width': 1440,
                        'height': 900,
                    },
                    'structured_context': {
                        'status': 'passed',
                        'artifact': self.artifacts['context.json'],
                    },
                    'same_node_screenshot': {
                        'status': 'passed',
                        'artifact': self.artifacts['screenshot.png'],
                    },
                },
            ],
            'sections': [
                {
                    'id': 'ranking',
                    'kind': 'ranking',
                    'frame_id': 'desktop-default',
                    'sizing': [
                        {
                            'target': 'ranking-grid',
                            'source': 'figma:15863:18454',
                            'expected': {
                                'intent': 'fluid',
                                'distribution': 'equal-tracks',
                                'gap_px': 0,
                            },
                            'actual': {
                                'intent': 'fluid',
                                'distribution': 'equal-tracks',
                                'gap_px': 0,
                            },
                            'tailwind': 'grid grid-cols-3 gap-0',
                            'computed': {
                                'display': 'grid',
                                'column_gap': 0,
                            },
                            'status': 'passed',
                        },
                    ],
                    'geometry': {
                        'status': 'passed',
                        'artifact': self.artifacts['geometry.json'],
                    },
                    'style': {
                        'tailwind_status': 'passed',
                        'computed_style_status': 'passed',
                        'artifact': self.artifacts['styles.json'],
                    },
                    'implementation': {
                        'crop': self.artifacts['crop.png'],
                        'comparison': self.artifacts['difference.png'],
                    },
                    'mismatch': {
                        'salience': 'none',
                        'status': 'closed',
                    },
                    'visual_layers': [
                        {
                            'id': 'rank-gradient',
                            'kind': 'gradient',
                            'visible': True,
                            'source': {
                                'status': 'resolved',
                                'locator': 'figma:15863:18454/rank-gradient',
                            },
                            'composition': {
                                'status': 'passed',
                                'artifact': self.artifacts['layers.json'],
                            },
                        },
                    ],
                    'motion_required': False,
                    'correction_ids': ['feedback-ranking'],
                },
                {
                    'id': 'lottery',
                    'kind': 'motion',
                    'frame_id': 'desktop-default',
                    'sizing': [
                        {
                            'target': 'lottery-grid',
                            'source': 'figma:15863:18454',
                            'expected': {
                                'intent': 'fixed',
                                'distribution': 'grid',
                                'gap_px': 8,
                            },
                            'actual': {
                                'intent': 'fixed',
                                'distribution': 'grid',
                                'gap_px': 8,
                            },
                            'tailwind': 'grid grid-cols-3 gap-m',
                            'computed': {
                                'display': 'grid',
                                'column_gap': 8,
                            },
                            'status': 'passed',
                        },
                    ],
                    'geometry': {
                        'status': 'passed',
                        'artifact': self.artifacts['geometry.json'],
                    },
                    'style': {
                        'tailwind_status': 'passed',
                        'computed_style_status': 'passed',
                        'artifact': self.artifacts['styles.json'],
                    },
                    'implementation': {
                        'crop': self.artifacts['crop.png'],
                        'comparison': self.artifacts['difference.png'],
                    },
                    'mismatch': {
                        'salience': 'none',
                        'status': 'closed',
                    },
                    'visual_layers': [],
                    'motion_required': True,
                    'correction_ids': [],
                },
            ],
            'responsive_matrix': [
                {
                    'id': 'h5-short',
                    'viewport': {
                        'kind': 'h5',
                        'width': 320,
                        'height': 568,
                        'short_height': True,
                    },
                    'full_interaction': {
                        'status': 'passed',
                        'trigger': True,
                        'scroll_owner': True,
                        'close_control': True,
                        'final_action': True,
                        'safe_area': True,
                        'horizontal_scroll': 'not-applicable',
                        'artifact': self.artifacts['interaction.json'],
                    },
                },
            ],
            'table_checks': [
                {
                    'id': 'ranking-columns',
                    'section_id': 'ranking',
                    'status': 'passed',
                    'artifact': self.artifacts['table.json'],
                    'first_column_edge': 16,
                    'last_column_edge': 16,
                    'scroll_width': 320,
                    'client_width': 320,
                    'columns': [
                        {
                            'id': 'uid',
                            'th': {
                                'start': 100,
                                'width': 120,
                                'center': 160,
                            },
                            'td': [
                                {
                                    'row': 'first',
                                    'start': 100,
                                    'width': 120,
                                    'center': 160,
                                },
                                {
                                    'row': 'last',
                                    'start': 100,
                                    'width': 120,
                                    'center': 160,
                                },
                                {
                                    'row': 'content-extreme',
                                    'start': 100,
                                    'width': 120,
                                    'center': 160,
                                },
                            ],
                        },
                    ],
                },
            ],
            'motion_checks': [
                {
                    'id': 'lottery-motion',
                    'section_id': 'lottery',
                    'kind': 'interaction',
                    'status': 'passed',
                    'trigger': True,
                    'order': True,
                    'input_lock': True,
                    'completion': True,
                    'unmount': True,
                    'artifact': self.artifacts['motion.json'],
                },
            ],
            'historical_reuse': [],
            'entry_surfaces': [],
            'asset_conversions': [
                {
                    'source': str(self.source_asset.relative_to(self.repo)),
                    'candidate': str(
                        self.candidate_asset.relative_to(self.repo)
                    ),
                    'target_format': 'webp',
                    'decision': 'accepted',
                    'before_bytes': self.source_asset.stat().st_size,
                    'after_bytes': self.candidate_asset.stat().st_size,
                    'source_dimensions': {'width': 1, 'height': 1},
                    'candidate_dimensions': {'width': 1, 'height': 1},
                    'alpha': {'source': 'opaque', 'candidate': 'opaque'},
                    'visual_comparison': {
                        'status': 'passed',
                        'tool': 'compare-assets-rgba',
                        'policy': 'lossless-exact',
                        'artifact': self.artifacts[
                            'asset-difference.json'
                        ],
                    },
                },
            ],
            'corrections': [
                {
                    'id': 'feedback-ranking',
                    'source': {
                        'kind': 'user-feedback',
                        'locator': 'session:PR-02107#ranking-columns',
                    },
                    'affected_rows': ['section:ranking'],
                    'status': 'closed',
                    'reverification': {
                        'status': 'passed',
                        'artifact': self.artifacts['correction.png'],
                    },
                },
            ],
            'api_contracts': [
                {'id': 'campaign-detail', 'status': 'verified'},
            ],
        }

    def run_validator(self, manifest, *extra_args):
        manifest_path = self.audit_dir / 'visual-evidence.json'
        manifest_path.write_text(json.dumps(manifest))
        return subprocess.run(
            [
                '/usr/bin/python3',
                str(SCRIPT),
                '--manifest',
                str(manifest_path),
                '--repo-root',
                str(self.repo),
                *extra_args,
                '--json',
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def materialized_template(self):
        def replace(value):
            if isinstance(value, dict):
                return {
                    key: replace(child)
                    for key, child in value.items()
                }
            if isinstance(value, list):
                return [replace(child) for child in value]
            if isinstance(value, str):
                if value.startswith('<') and value.endswith('>'):
                    return 'fixture'
                if ' | ' in value:
                    return value.split(' | ', 1)[0]
            if value == 0 and not isinstance(value, bool):
                return 1
            return value

        manifest = replace(json.loads(TEMPLATE.read_text()))
        manifest['task'].update(
            {
                'id': 'PR-02107',
                'repository': str(self.repo),
                'mode': 'feature-delivery',
                'route': '/contract-carnival',
                'branch': 'feature/PR-02107',
                'locale': 'zh-CN',
                'target_paths': ['apps/web/page.tsx'],
            }
        )
        manifest['claim'] = {
            'status': 'pending',
            'level': 'presentation-slice-verified',
        }
        return manifest

    def test_template_defines_the_canonical_evidence_sections(self):
        template = json.loads(TEMPLATE.read_text())

        for key in (
            'schema_version',
            'task',
            'claim',
            'required_viewports',
            'frames',
            'sections',
            'responsive_matrix',
            'table_checks',
            'motion_checks',
            'historical_reuse',
            'entry_surfaces',
            'asset_conversions',
            'corrections',
            'api_contracts',
        ):
            self.assertIn(key, template)
        for key in (
            'first_column_edge',
            'last_column_edge',
            'scroll_width',
            'client_width',
        ):
            self.assertIn(key, template['table_checks'][0])
        self.assertIn('kind', template['motion_checks'][0])
        self.assertIn('observer', template['motion_checks'][0])
        for key in (
            'viewport',
            'state',
            'source_component',
            'source_capability',
            'source_asset',
            'requested_part',
        ):
            self.assertIn(key, template['historical_reuse'][0])
        self.assertIn(
            'configuration_location',
            template['entry_surfaces'][0],
        )

    def test_shipped_template_materializes_to_a_valid_v2_draft(self):
        result = self.run_validator(
            self.materialized_template(),
            '--draft',
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['schema_valid'])
        self.assertFalse(payload['claim_ready'])

    def test_a_complete_manifest_passes(self):
        written = self.run_validator(
            self.valid_manifest(),
            '--write-receipt',
        )
        result = self.run_validator(self.valid_manifest())

        self.assertEqual(
            0,
            written.returncode,
            written.stdout + written.stderr,
        )
        self.assertTrue(
            (self.audit_dir / 'validation-receipt.json').is_file()
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['valid'])
        self.assertTrue(payload['schema_valid'])
        self.assertTrue(payload['claim_ready'])
        self.assertEqual([], payload['errors'])
        self.assertEqual([], payload['schema_errors'])
        self.assertEqual([], payload['claim_errors'])

    def test_presentation_claim_can_report_an_unresolved_api(self):
        manifest = self.valid_manifest()
        manifest['api_contracts'][0]['status'] = 'waiting'

        result = self.run_validator(manifest, '--write-receipt')

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['claim_ready'])

    def test_one_shot_observer_policy_can_pass(self):
        manifest = self.valid_manifest()
        motion = manifest['motion_checks'][0]
        motion['kind'] = 'intersection-observer'
        motion['observer'] = observer_evidence(reentry_policy='once')
        artifact = self.audit_dir / 'observer-motion.json'
        artifact.write_text(
            json.dumps(
                {
                    'source': 'playwright',
                    'status': 'passed',
                    'section_id': motion['section_id'],
                    'kind': motion['kind'],
                    'checks': {
                        field: motion[field]
                        for field in (
                            'trigger',
                            'order',
                            'input_lock',
                            'completion',
                            'unmount',
                        )
                    },
                    'observer': motion['observer'],
                }
            )
        )
        motion['artifact'] = str(artifact.relative_to(self.repo))

        result = self.run_validator(manifest, '--write-receipt')

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['claim_ready'])

    def test_verified_claim_without_a_receipt_fails_closed(self):
        result = self.run_validator(self.valid_manifest())

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertIn(
            'receipt.missing',
            {error['code'] for error in payload['claim_errors']},
        )

    def test_receipt_detects_a_changed_manifest(self):
        manifest = self.valid_manifest()
        written = self.run_validator(manifest, '--write-receipt')
        self.assertEqual(0, written.returncode, written.stdout)
        manifest['task']['route'] = '/changed-route'

        result = self.run_validator(manifest)

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertIn(
            'receipt.manifest_stale',
            {error['code'] for error in payload['claim_errors']},
        )

    def test_receipt_detects_a_changed_target_file(self):
        manifest = self.valid_manifest()
        written = self.run_validator(manifest, '--write-receipt')
        self.assertEqual(0, written.returncode, written.stdout)
        self.target_file.write_text(
            'export default function ChangedPage() {}'
        )

        result = self.run_validator(manifest)

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertIn(
            'receipt.target_stale',
            {error['code'] for error in payload['claim_errors']},
        )

    def test_receipt_detects_a_changed_artifact(self):
        manifest = self.valid_manifest()
        written = self.run_validator(manifest, '--write-receipt')
        self.assertEqual(0, written.returncode, written.stdout)
        (self.audit_dir / 'geometry.json').write_text('{"changed": true}')

        result = self.run_validator(manifest)

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertIn(
            'receipt.artifact_stale',
            {error['code'] for error in payload['claim_errors']},
        )

    def test_receipt_detects_a_changed_git_snapshot(self):
        manifest = self.valid_manifest()
        written = self.run_validator(manifest, '--write-receipt')
        self.assertEqual(0, written.returncode, written.stdout)
        unrelated = self.repo / 'unrelated.txt'
        unrelated.write_text('new commit')
        subprocess.run(
            ['git', 'add', 'unrelated.txt'],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ['git', 'commit', '-qm', 'advance head'],
            cwd=self.repo,
            check=True,
        )

        result = self.run_validator(manifest)

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertIn(
            'receipt.git_stale',
            {error['code'] for error in payload['claim_errors']},
        )

    def test_receipt_binds_an_uncommitted_candidate_snapshot(self):
        untracked = self.repo / 'untracked-candidate.tsx'
        untracked.write_text('before')
        manifest = self.valid_manifest()

        written = self.run_validator(manifest, '--write-receipt')
        fresh = self.run_validator(manifest)

        self.assertEqual(0, written.returncode, written.stdout)
        self.assertEqual(0, fresh.returncode, fresh.stdout)

        untracked.write_text('after')
        stale = self.run_validator(manifest)

        self.assertNotEqual(0, stale.returncode)
        payload = json.loads(stale.stdout)
        self.assertIn(
            'receipt.git_stale',
            {error['code'] for error in payload['claim_errors']},
        )

    def test_pending_claim_requires_explicit_draft_mode(self):
        manifest = self.valid_manifest()
        manifest['claim']['status'] = 'pending'

        completion = self.run_validator(manifest)
        draft = self.run_validator(manifest, '--draft')

        self.assertNotEqual(0, completion.returncode)
        completion_payload = json.loads(completion.stdout)
        self.assertTrue(completion_payload['schema_valid'])
        self.assertFalse(completion_payload['claim_ready'])
        self.assertIn(
            'claim.not_verified',
            {
                error['code']
                for error in completion_payload['claim_errors']
            },
        )
        self.assertEqual(0, draft.returncode, draft.stdout + draft.stderr)
        draft_payload = json.loads(draft.stdout)
        self.assertTrue(draft_payload['schema_valid'])
        self.assertFalse(draft_payload['claim_ready'])
        self.assertTrue(draft_payload['valid'])

    def test_draft_mode_rejects_a_verified_claim(self):
        result = self.run_validator(self.valid_manifest(), '--draft')

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertIn(
            'claim.draft_status',
            {error['code'] for error in payload['claim_errors']},
        )

    def test_cli_rejects_an_unsupported_broader_claim(self):
        result = self.run_validator(
            self.valid_manifest(),
            '--require-claim',
            'feature-regression-verified',
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn('invalid choice', result.stderr)

    def test_no_visual_mode_can_claim_feature_regression(self):
        for mode in (
            'exact-node-implementation',
            'feature-delivery',
            'slice-implementation',
            'audit-existing',
        ):
            with self.subTest(mode=mode):
                manifest = self.valid_manifest()
                manifest['task']['mode'] = mode
                manifest['claim']['level'] = (
                    'feature-regression-verified'
                )

                result = self.run_validator(
                    manifest,
                    '--write-receipt',
                )

                self.assertNotEqual(0, result.returncode)
                payload = json.loads(result.stdout)
                self.assertIn(
                    'claim.level',
                    {
                        error['code']
                        for error in payload['schema_errors']
                    },
                )

    def test_draft_and_required_claim_are_mutually_exclusive(self):
        result = self.run_validator(
            self.valid_manifest(),
            '--draft',
            '--require-claim',
            'presentation-slice-verified',
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn('argument', result.stderr)

    def test_schema_rejects_unsupported_or_malformed_values(self):
        cases = {}

        unsupported_version = self.valid_manifest()
        unsupported_version['schema_version'] = 'garbage'
        cases['schema-version'] = (
            unsupported_version,
            'schema.version',
        )

        unknown_mode = self.valid_manifest()
        unknown_mode['task']['mode'] = 'unknown'
        cases['task-mode'] = (unknown_mode, 'task.mode')

        misspelled_status = self.valid_manifest()
        misspelled_status['claim']['status'] = 'verfied'
        cases['claim-status'] = (misspelled_status, 'claim.status')

        invalid_collection = self.valid_manifest()
        invalid_collection['sections'] = {}
        cases['collection-type'] = (
            invalid_collection,
            'manifest.collection_type',
        )

        placeholder = self.valid_manifest()
        placeholder['task']['branch'] = '<branch>'
        cases['placeholder'] = (placeholder, 'manifest.placeholder')

        unknown_field = self.valid_manifest()
        unknown_field['frames'][0]['structured_context'][
            'statuz'
        ] = 'passed'
        cases['unknown-field'] = (
            unknown_field,
            'schema.unknown_field',
        )

        malformed_context = self.valid_manifest()
        malformed_context['frames'][0]['structured_context'] = []
        cases['nested-context-type'] = (
            malformed_context,
            'schema.object_type',
        )

        malformed_geometry = self.valid_manifest()
        malformed_geometry['sections'][0]['geometry'] = []
        cases['nested-geometry-type'] = (
            malformed_geometry,
            'schema.object_type',
        )

        malformed_viewport = self.valid_manifest()
        malformed_viewport['responsive_matrix'][0]['viewport'] = []
        cases['nested-viewport-type'] = (
            malformed_viewport,
            'schema.object_type',
        )

        malformed_column = self.valid_manifest()
        malformed_column['table_checks'][0]['columns'] = [[]]
        cases['nested-column-type'] = (
            malformed_column,
            'schema.object_type',
        )

        malformed_reverification = self.valid_manifest()
        malformed_reverification['corrections'][0][
            'reverification'
        ] = []
        cases['nested-reverification-type'] = (
            malformed_reverification,
            'schema.object_type',
        )

        unhashable_section_kind = self.valid_manifest()
        unhashable_section_kind['sections'][0]['kind'] = []
        cases['section-kind-type'] = (
            unhashable_section_kind,
            'schema.string_type',
        )

        unhashable_correction = self.valid_manifest()
        unhashable_correction['sections'][0]['correction_ids'] = [[]]
        cases['correction-id-type'] = (
            unhashable_correction,
            'schema.string_type',
        )

        unhashable_table_reference = self.valid_manifest()
        unhashable_table_reference['table_checks'][0][
            'section_id'
        ] = []
        cases['table-reference-type'] = (
            unhashable_table_reference,
            'schema.string_type',
        )

        unhashable_claim_status = self.valid_manifest()
        unhashable_claim_status['claim']['status'] = []
        cases['claim-status-type'] = (
            unhashable_claim_status,
            'claim.status',
        )

        oversized_viewport = self.valid_manifest()
        oversized_viewport['frames'][0]['viewport']['width'] = 10**10000
        cases['oversized-viewport'] = (
            oversized_viewport,
            'schema.viewport_dimension',
        )

        empty_evidence = self.valid_manifest()
        empty_evidence['frames'][0]['structured_context'] = {}
        cases['evidence-required-fields'] = (
            empty_evidence,
            'schema.required',
        )

        bad_evidence_types = self.valid_manifest()
        bad_evidence_types['frames'][0]['structured_context'] = {
            'status': [],
            'artifact': 1,
        }
        cases['evidence-scalar-types'] = (
            bad_evidence_types,
            'schema.string_type',
        )

        bad_interaction_bool = self.valid_manifest()
        bad_interaction_bool['responsive_matrix'][0][
            'full_interaction'
        ]['trigger'] = []
        cases['interaction-boolean-type'] = (
            bad_interaction_bool,
            'schema.boolean',
        )

        empty_style = self.valid_manifest()
        empty_style['sections'][0]['style'] = {}
        cases['style-required-fields'] = (
            empty_style,
            'schema.required',
        )

        missing_table_metric = self.valid_manifest()
        missing_table_metric['table_checks'][0].pop('scroll_width')
        cases['table-metric-required'] = (
            missing_table_metric,
            'schema.number',
        )

        invalid_observer_threshold = self.valid_manifest()
        invalid_observer_threshold['motion_checks'][0].update(
            {
                'kind': 'intersection-observer',
                'observer': observer_evidence(threshold=2),
            }
        )
        cases['observer-threshold-range'] = (
            invalid_observer_threshold,
            'schema.number',
        )

        for name, (manifest, expected_code) in cases.items():
            with self.subTest(name=name):
                result = self.run_validator(manifest)
                self.assertNotEqual(0, result.returncode)
                self.assertNotIn('Traceback', result.stderr)
                payload = json.loads(result.stdout)
                self.assertFalse(payload['schema_valid'])
                codes = {
                    error['code']
                    for error in payload['schema_errors']
                }
                self.assertIn(expected_code, codes)

    def test_draft_allows_unfinished_evidence_rows(self):
        manifest = self.valid_manifest()
        manifest['claim']['status'] = 'pending'
        manifest['frames'][0]['structured_context']['status'] = 'pending'
        manifest['sections'][0]['geometry']['status'] = 'failed'
        manifest['responsive_matrix'][0]['full_interaction'][
            'status'
        ] = 'pending'

        result = self.run_validator(manifest, '--draft')

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['schema_valid'])
        self.assertFalse(payload['claim_ready'])

    def test_visual_manifest_cannot_claim_release_readiness(self):
        for level in (
            'feature-regression-verified',
            'release-ready',
            'released',
        ):
            with self.subTest(level=level):
                manifest = self.valid_manifest()
                manifest['claim']['level'] = level

                result = self.run_validator(manifest)

                self.assertNotEqual(0, result.returncode)
                payload = json.loads(result.stdout)
                self.assertIn(
                    'claim.level',
                    {
                        error['code']
                        for error in payload['schema_errors']
                    },
                )

    def test_v1_manifest_error_includes_a_safe_migration_path(self):
        manifest = self.valid_manifest()
        manifest['schema_version'] = '1.0'

        result = self.run_validator(manifest, '--draft')

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        version_error = next(
            error
            for error in payload['schema_errors']
            if error['code'] == 'schema.version'
        )
        self.assertIn(
            'assets/templates/visual-evidence.json',
            version_error['message'],
        )
        self.assertIn('do not promote a v1 claim', version_error['message'])

    def test_visual_completion_is_blocked_by_each_missing_evidence_class(self):
        cases = {}

        missing_node = self.valid_manifest()
        missing_node['frames'][0]['structured_context']['status'] = 'pending'
        cases['exact-node-context'] = (missing_node, 'frame.context')

        missing_layer = self.valid_manifest()
        missing_layer['sections'][0]['visual_layers'][0]['source'][
            'status'
        ] = 'pending'
        cases['visible-layer-source'] = (missing_layer, 'layer.source')

        high_mismatch = self.valid_manifest()
        high_mismatch['sections'][0]['mismatch'] = {
            'salience': 'high',
            'status': 'open',
        }
        cases['high-salience-mismatch'] = (
            high_mismatch,
            'section.high_mismatch',
        )

        short_h5 = self.valid_manifest()
        short_h5['responsive_matrix'][0]['full_interaction'][
            'final_action'
        ] = False
        cases['short-height-interaction'] = (
            short_h5,
            'responsive.short_height',
        )

        table = self.valid_manifest()
        table['table_checks'][0]['columns'][0]['td'][0]['center'] = 170
        cases['table-shared-measurement'] = (
            table,
            'table.column_alignment',
        )

        missing_representative_row = self.valid_manifest()
        missing_representative_row['table_checks'][0]['columns'][0][
            'td'
        ] = missing_representative_row['table_checks'][0]['columns'][0][
            'td'
        ][:2]
        cases['table-representative-rows'] = (
            missing_representative_row,
            'table.representative_rows',
        )

        impossible_scroll_metrics = self.valid_manifest()
        impossible_scroll_metrics['table_checks'][0][
            'scroll_width'
        ] = 300
        impossible_scroll_metrics['table_checks'][0][
            'client_width'
        ] = 320
        cases['table-scroll-metrics'] = (
            impossible_scroll_metrics,
            'table.scroll_metrics',
        )

        motion = self.valid_manifest()
        motion['motion_checks'][0]['input_lock'] = False
        cases['motion-lifecycle'] = (motion, 'motion.input_lock')

        observer_motion = self.valid_manifest()
        observer_motion['motion_checks'][0].update(
            {
                'kind': 'intersection-observer',
                'observer': observer_evidence(
                    disconnect_verified=False,
                ),
            }
        )
        cases['motion-observer-lifecycle'] = (
            observer_motion,
            'motion.observer',
        )

        correction = self.valid_manifest()
        correction['corrections'][0]['reverification']['status'] = 'pending'
        cases['correction-reverification'] = (
            correction,
            'correction.reverification',
        )

        webp = self.valid_manifest()
        webp['asset_conversions'][0]['visual_comparison'][
            'status'
        ] = 'unverified'
        cases['webp-no-visual-comparison'] = (
            webp,
            'asset.webp_comparison',
        )

        required_viewport = self.valid_manifest()
        required_viewport['responsive_matrix'] = []
        cases['required-viewport'] = (
            required_viewport,
            'responsive.required_viewport',
        )

        sizing = self.valid_manifest()
        sizing['sections'][0]['sizing'][0]['actual'][
            'distribution'
        ] = 'justify-between'
        cases['layout-constraint'] = (
            sizing,
            'layout.constraint',
        )

        artifact_scope = self.valid_manifest()
        outside_artifact = self.repo / 'package.json'
        outside_artifact.write_text('{}')
        artifact_scope['frames'][0]['structured_context'][
            'artifact'
        ] = 'package.json'
        cases['artifact-scope'] = (
            artifact_scope,
            'artifact.scope',
        )

        interaction_artifact = self.valid_manifest()
        invalid_interaction = self.audit_dir / 'invalid-interaction.json'
        invalid_interaction.write_text('{}')
        interaction_artifact['responsive_matrix'][0]['full_interaction'][
            'artifact'
        ] = str(invalid_interaction.relative_to(self.repo))
        cases['interaction-artifact'] = (
            interaction_artifact,
            'responsive.interaction_artifact',
        )

        invalid_context_payload = self.valid_manifest()
        invalid_context_path = self.audit_dir / 'invalid-context.json'
        invalid_context_path.write_text('{}')
        invalid_context_payload['frames'][0]['structured_context'][
            'artifact'
        ] = str(invalid_context_path.relative_to(self.repo))
        cases['context-artifact-payload'] = (
            invalid_context_payload,
            'artifact.json_evidence',
        )

        invalid_screenshot = self.valid_manifest()
        invalid_screenshot_path = self.audit_dir / 'invalid-screenshot.png'
        invalid_screenshot_path.write_bytes(b'evidence')
        invalid_screenshot['frames'][0]['same_node_screenshot'][
            'artifact'
        ] = str(invalid_screenshot_path.relative_to(self.repo))
        cases['screenshot-image-payload'] = (
            invalid_screenshot,
            'artifact.image_invalid',
        )

        header_only_screenshot = self.valid_manifest()
        header_only_path = self.audit_dir / 'header-only.webp'
        vp8x_header = bytes([0, 0, 0, 0]) + (0).to_bytes(
            3,
            'little',
        ) + (0).to_bytes(3, 'little')
        header_only_path.write_bytes(
            b'RIFF'
            + struct.pack('<I', 4 + 8 + len(vp8x_header))
            + b'WEBP'
            + b'VP8X'
            + struct.pack('<I', len(vp8x_header))
            + vp8x_header
        )
        header_only_screenshot['frames'][0]['same_node_screenshot'][
            'artifact'
        ] = str(header_only_path.relative_to(self.repo))
        cases['screenshot-header-only-payload'] = (
            header_only_screenshot,
            'artifact.image_invalid',
        )

        invalid_table_payload = self.valid_manifest()
        invalid_table_path = self.audit_dir / 'invalid-table.json'
        invalid_table_path.write_text('{}')
        invalid_table_payload['table_checks'][0]['artifact'] = str(
            invalid_table_path.relative_to(self.repo)
        )
        cases['table-artifact-payload'] = (
            invalid_table_payload,
            'artifact.json_evidence',
        )

        missing_candidate = self.valid_manifest()
        missing_candidate['asset_conversions'][0][
            'candidate'
        ] = 'assets/missing.webp'
        cases['webp-missing-candidate'] = (
            missing_candidate,
            'asset.candidate',
        )

        fake_comparison = self.valid_manifest()
        fake_path = self.audit_dir / 'fake-comparison.json'
        fake_path.write_text(
            json.dumps(
                {
                    'source_sha256': 'fake',
                    'candidate_sha256': 'fake',
                    'tool': 'fake-comparator',
                    'status': 'passed',
                }
            )
        )
        fake_comparison['asset_conversions'][0]['visual_comparison'] = {
            'status': 'passed',
            'tool': 'fake-comparator',
            'artifact': str(fake_path.relative_to(self.repo)),
        }
        cases['webp-fake-comparison'] = (
            fake_comparison,
            'schema.enum',
        )

        forged_zero_difference = self.valid_manifest()
        different_candidate = self.candidate_asset.with_name(
            'different.webp'
        )
        different_candidate.write_bytes(
            base64.b64decode(
                'UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEA'
                'DsD+JaQAA3AAAAAA'
            )
        )
        forged_zero_difference['asset_conversions'][0]['candidate'] = str(
            different_candidate.relative_to(self.repo)
        )
        forged_zero_difference['asset_conversions'][0][
            'after_bytes'
        ] = different_candidate.stat().st_size
        forged_payload = json.loads(
            (self.audit_dir / 'asset-difference.json').read_text()
        )
        forged_payload['candidate_sha256'] = hashlib.sha256(
            different_candidate.read_bytes()
        ).hexdigest()
        forged_path = self.audit_dir / 'forged-zero-difference.json'
        forged_path.write_text(json.dumps(forged_payload))
        forged_zero_difference['asset_conversions'][0][
            'visual_comparison'
        ]['artifact'] = str(forged_path.relative_to(self.repo))
        cases['webp-forged-zero-difference'] = (
            forged_zero_difference,
            'asset.webp_comparison',
        )

        undecodable_candidate = self.valid_manifest()
        malformed_candidate = self.candidate_asset.with_name(
            'malformed.webp'
        )
        vp8x = bytes([0, 0, 0, 0]) + (0).to_bytes(
            3,
            'little',
        ) + (0).to_bytes(3, 'little')
        malformed_candidate.write_bytes(
            b'RIFF'
            + struct.pack('<I', 4 + 8 + len(vp8x))
            + b'WEBP'
            + b'VP8X'
            + struct.pack('<I', len(vp8x))
            + vp8x
        )
        undecodable_candidate['asset_conversions'][0]['candidate'] = str(
            malformed_candidate.relative_to(self.repo)
        )
        undecodable_candidate['asset_conversions'][0][
            'after_bytes'
        ] = malformed_candidate.stat().st_size
        cases['webp-undecodable-candidate'] = (
            undecodable_candidate,
            'asset.rgba_decode',
        )

        historical_evidence = self.valid_manifest()
        historical_evidence['historical_reuse'] = [
            {
                'route': '/historical',
                'viewport': {
                    'kind': 'desktop',
                    'width': 1440,
                    'height': 900,
                },
                'state': 'default',
                'source_component': 'ExistingComponent',
                'source_capability': 'useExistingFeature',
                'source_asset': 'not-applicable',
                'requested_part': 'ranking-shell',
                'decision': 'reuse',
                'evidence': 'apps/web/page.tsx',
            },
        ]
        cases['historical-evidence-scope'] = (
            historical_evidence,
            'artifact.scope',
        )

        entry_evidence = self.valid_manifest()
        entry_evidence['entry_surfaces'] = [
            {
                'kind': 'canonical-route',
                'owner': 'apps/web',
                'source': 'repository-route',
                'configuration_location': 'apps/web/src/app',
                'status': 'verified',
                'evidence': (
                    'output-tdd/figma-audits/PR-02107/'
                    'missing-entry.json'
                ),
            },
        ]
        cases['entry-evidence-missing'] = (
            entry_evidence,
            'entry_surface.evidence',
        )

        for name, (manifest, expected_code) in cases.items():
            with self.subTest(name=name):
                result = self.run_validator(manifest)
                self.assertNotEqual(0, result.returncode)
                payload = json.loads(result.stdout)
                codes = {error['code'] for error in payload['errors']}
                self.assertIn(expected_code, codes)


if __name__ == '__main__':
    unittest.main()
