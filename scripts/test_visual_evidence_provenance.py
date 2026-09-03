import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from visual_evidence_provenance import (
    SnapshotError,
    build_receipt,
    validate_receipt,
)


class VisualEvidenceProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.repo = Path(self.temp_dir.name) / 'repo'
        self.repo.mkdir()
        (self.repo / '.gitignore').write_text('output-tdd/\n')
        self.target = self.repo / 'apps/web/page.tsx'
        self.target.parent.mkdir(parents=True)
        self.target.write_text('export default function Page() {}')
        subprocess.run(['git', 'init', '-q'], cwd=self.repo, check=True)
        subprocess.run(
            ['git', 'config', 'user.email', 'tests@example.com'],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'Provenance Tests'],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(['git', 'add', '.'], cwd=self.repo, check=True)
        subprocess.run(
            ['git', 'commit', '-qm', 'fixture'],
            cwd=self.repo,
            check=True,
        )
        self.audit_dir = (
            self.repo / 'output-tdd/figma-audits/receipt-test'
        )
        self.audit_dir.mkdir(parents=True)
        self.manifest = self.audit_dir / 'visual-evidence.json'
        self.manifest.write_text('{"schema_version":"2.0"}')
        self.artifact = self.audit_dir / 'geometry.json'
        self.artifact.write_text('{"status":"passed"}')
        self.claim = {
            'status': 'verified',
            'level': 'presentation-slice-verified',
        }

    def build(self):
        return build_receipt(
            manifest_path=self.manifest,
            repo_root=self.repo,
            target_paths=['apps/web/page.tsx'],
            artifacts={self.artifact.resolve()},
            claim=self.claim,
        )

    def test_receipt_records_reproducible_git_file_and_artifact_state(self):
        receipt = self.build()

        self.assertEqual('1.0', receipt['schema_version'])
        self.assertEqual('2.0', receipt['validator_version'])
        self.assertEqual(
            [
                'scripts/audit_assets.py',
                'scripts/compare_assets_rgba.py',
                'scripts/validate_visual_evidence.py',
                'scripts/visual_evidence_provenance.py',
            ],
            [item['path'] for item in receipt['validator_build']],
        )
        self.assertTrue(
            all(
                len(item['sha256']) == 64
                for item in receipt['validator_build']
            )
        )
        self.assertEqual(64, len(receipt['manifest_sha256']))
        self.assertTrue(receipt['git']['head'])
        self.assertTrue(receipt['git']['tree'])
        self.assertFalse(receipt['git']['dirty'])
        self.assertEqual(
            ['apps/web/page.tsx'],
            [item['path'] for item in receipt['targets']],
        )
        self.assertEqual(
            ['output-tdd/figma-audits/receipt-test/geometry.json'],
            [item['path'] for item in receipt['artifacts']],
        )
        self.assertEqual([], validate_receipt(
            receipt=receipt,
            manifest_path=self.manifest,
            repo_root=self.repo,
            target_paths=['apps/web/page.tsx'],
            artifacts={self.artifact.resolve()},
            claim=self.claim,
        ))

    def stale_codes(self, receipt):
        errors = validate_receipt(
            receipt=receipt,
            manifest_path=self.manifest,
            repo_root=self.repo,
            target_paths=['apps/web/page.tsx'],
            artifacts={self.artifact.resolve()},
            claim=self.claim,
        )
        return {error['code'] for error in errors}

    def test_receipt_detects_a_changed_manifest(self):
        receipt = self.build()
        self.manifest.write_text(
            '{"schema_version":"2.0","changed":true}'
        )

        self.assertIn(
            'receipt.manifest_stale',
            self.stale_codes(receipt),
        )

    def test_receipt_detects_a_changed_target(self):
        receipt = self.build()
        self.target.write_text('changed')

        self.assertIn('receipt.target_stale', self.stale_codes(receipt))

    def test_receipt_detects_a_changed_artifact(self):
        receipt = self.build()
        self.artifact.write_text('changed')

        self.assertIn(
            'receipt.artifact_stale',
            self.stale_codes(receipt),
        )

    def test_receipt_detects_a_changed_git_snapshot(self):
        receipt = self.build()
        self.advance_git_head()

        self.assertIn('receipt.git_stale', self.stale_codes(receipt))

    def test_receipt_detects_a_changed_validator_build(self):
        receipt = self.build()
        receipt['validator_build'][0]['sha256'] = '0' * 64

        self.assertIn(
            'receipt.validator_build_stale',
            self.stale_codes(receipt),
        )

    def test_claim_receipt_binds_untracked_file_contents(self):
        (self.repo / 'untracked.txt').write_text('before')

        receipt = self.build()

        self.assertTrue(receipt['git']['dirty'])
        self.assertEqual(
            ['untracked.txt'],
            [
                record['path']
                for record in receipt['git']['untracked']
            ],
        )
        self.assertEqual(set(), self.stale_codes(receipt))

        (self.repo / 'untracked.txt').write_text('after')

        self.assertIn('receipt.git_stale', self.stale_codes(receipt))

    def test_claim_receipt_binds_tracked_dirty_content(self):
        (self.repo / '.gitignore').write_text(
            'output-tdd/\nfirst-change\n'
        )

        receipt = self.build()

        self.assertTrue(receipt['git']['dirty'])
        first_diff = receipt['git']['tracked_diff_sha256']

        (self.repo / '.gitignore').write_text(
            'output-tdd/\nsecond-change\n'
        )

        self.assertNotEqual(
            first_diff,
            build_receipt(
                manifest_path=self.manifest,
                repo_root=self.repo,
                target_paths=['apps/web/page.tsx'],
                artifacts={self.artifact.resolve()},
                claim=self.claim,
            )['git']['tracked_diff_sha256'],
        )
        self.assertIn('receipt.git_stale', self.stale_codes(receipt))

    def test_claim_receipt_requires_the_audit_directory_to_be_ignored(self):
        other_repo = Path(self.temp_dir.name) / 'not-ignored'
        other_repo.mkdir()
        target = other_repo / 'page.tsx'
        target.write_text('export default function Page() {}')
        audit_dir = (
            other_repo / 'output-tdd/figma-audits/not-ignored'
        )
        audit_dir.mkdir(parents=True)
        manifest = audit_dir / 'visual-evidence.json'
        manifest.write_text('{"schema_version":"2.0"}')
        artifact = audit_dir / 'geometry.json'
        artifact.write_text('{}')
        subprocess.run(['git', 'init', '-q'], cwd=other_repo, check=True)
        subprocess.run(
            ['git', 'config', 'user.email', 'tests@example.com'],
            cwd=other_repo,
            check=True,
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'Provenance Tests'],
            cwd=other_repo,
            check=True,
        )
        subprocess.run(['git', 'add', '.'], cwd=other_repo, check=True)
        subprocess.run(
            ['git', 'commit', '-qm', 'fixture'],
            cwd=other_repo,
            check=True,
        )

        with self.assertRaisesRegex(SnapshotError, 'must be ignored'):
            build_receipt(
                manifest_path=manifest,
                repo_root=other_repo,
                target_paths=['page.tsx'],
                artifacts={artifact.resolve()},
                claim=self.claim,
            )

    def advance_git_head(self):
        path = self.repo / 'unrelated.txt'
        path.write_text('advance')
        subprocess.run(
            ['git', 'add', 'unrelated.txt'],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ['git', 'commit', '-qm', 'advance'],
            cwd=self.repo,
            check=True,
        )

    def test_receipt_is_json_serializable(self):
        payload = json.loads(json.dumps(self.build()))

        self.assertEqual(self.claim, payload['claim'])


if __name__ == '__main__':
    unittest.main()
