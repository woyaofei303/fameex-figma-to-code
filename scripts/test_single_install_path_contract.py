from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROOT = '/Users/julian/.codex/skills/fameex-figma-to-code'
OLD_ROOT = '/Users/julian/fameex-figma-to-code'


class SingleInstallPathContractTest(unittest.TestCase):
    def test_readme_uses_only_the_installed_git_repository(self):
        readme = (ROOT / 'README.md').read_text()

        self.assertIn(CANONICAL_ROOT, readme)
        self.assertNotIn(OLD_ROOT, readme)
        self.assertNotIn('源码仓库：', readme)
        self.assertNotIn('运行时 Skill：', readme)
        self.assertNotIn('同步到运行时目录', readme)

    def test_feature_manifest_references_canonical_visual_evidence(self):
        template = (ROOT / 'assets/templates/feature-manifest.yaml').read_text()

        self.assertIn('visual_evidence:', template)
        self.assertIn(
            'output-tdd/figma-audits/<task>/visual-evidence.json',
            template,
        )

    def test_workflows_use_one_canonical_manifest_and_validator(self):
        references = '\n'.join(
            (ROOT / path).read_text()
            for path in (
                'references/exact-node-workflow.md',
                'references/visual-fidelity-loop.md',
                'references/product-delivery-workflow.md',
            )
        )

        self.assertIn('assets/templates/visual-evidence.json', references)
        self.assertIn('scripts/validate_visual_evidence.py', references)
        self.assertIn('scripts/search_codex_history.py', references)
        self.assertIn('scripts/audit_assets.py', references)
        self.assertIn(
            'output-tdd/figma-audits/<task>/visual-evidence.json',
            references,
        )
        self.assertIn('required_viewports', references)
        self.assertIn('expected', references)
        self.assertIn('actual', references)
        self.assertIn('source: playwright', references)
        self.assertIn('source_sha256', references)
        self.assertIn('candidate_sha256', references)


if __name__ == '__main__':
    unittest.main()
