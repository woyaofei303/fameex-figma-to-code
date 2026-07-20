import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/validate_visual_evidence.py'
TEMPLATE = ROOT / 'assets/templates/visual-evidence.json'


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
                path.write_text('{}')
            else:
                path.write_bytes(b'evidence')
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
        self.source_asset.write_bytes(
            b'\x89PNG\r\n\x1a\n'
            + struct.pack('>I', 13)
            + b'IHDR'
            + struct.pack('>IIBBBBB', 600, 400, 8, 6, 0, 0, 0)
            + b'\x00\x00\x00\x00'
            + (b'source-padding' * 20)
        )
        self.candidate_asset = asset_dir / 'hero.webp'
        vp8x = (
            bytes([0x10, 0, 0, 0])
            + (599).to_bytes(3, 'little')
            + (399).to_bytes(3, 'little')
        )
        self.candidate_asset.write_bytes(
            b'RIFF'
            + struct.pack('<I', 4 + 8 + len(vp8x))
            + b'WEBP'
            + b'VP8X'
            + struct.pack('<I', len(vp8x))
            + vp8x
        )
        self.source_sha256 = hashlib.sha256(
            self.source_asset.read_bytes()
        ).hexdigest()
        self.candidate_sha256 = hashlib.sha256(
            self.candidate_asset.read_bytes()
        ).hexdigest()
        (self.audit_dir / 'asset-difference.json').write_text(
            json.dumps(
                {
                    'source_sha256': self.source_sha256,
                    'candidate_sha256': self.candidate_sha256,
                    'tool': 'pixelmatch',
                    'status': 'passed',
                    'metric': 'rgba',
                    'pixels_compared': 240000,
                    'different_pixels': 0,
                    'max_channel_delta': 0,
                    'alpha_different_pixels': 0,
                }
            )
        )

    def valid_manifest(self):
        return {
            'schema_version': '1.0',
            'task': {
                'id': 'PR-02107',
                'repository': str(self.repo),
                'mode': 'feature-delivery',
                'route': '/contract-carnival',
            },
            'claim': {
                'status': 'verified',
                'level': 'feature-complete',
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
                            ],
                        },
                    ],
                },
            ],
            'motion_checks': [
                {
                    'id': 'lottery-motion',
                    'section_id': 'lottery',
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
                    'source_dimensions': {'width': 600, 'height': 400},
                    'candidate_dimensions': {'width': 600, 'height': 400},
                    'alpha': {'source': 'present', 'candidate': 'present'},
                    'visual_comparison': {
                        'status': 'passed',
                        'tool': 'pixelmatch',
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

    def run_validator(self, manifest):
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
                '--json',
            ],
            check=False,
            capture_output=True,
            text=True,
        )

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

    def test_a_complete_manifest_passes(self):
        result = self.run_validator(self.valid_manifest())

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['valid'])
        self.assertEqual([], payload['errors'])

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

        motion = self.valid_manifest()
        motion['motion_checks'][0]['input_lock'] = False
        cases['motion-lifecycle'] = (motion, 'motion.input_lock')

        correction = self.valid_manifest()
        correction['corrections'][0]['reverification']['status'] = 'pending'
        cases['correction-reverification'] = (
            correction,
            'correction.reverification',
        )

        api = self.valid_manifest()
        api['api_contracts'][0]['status'] = 'waiting'
        cases['api-overclaim'] = (api, 'claim.api_unresolved')

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
            'asset.webp_comparison',
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
