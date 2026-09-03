from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ExactNodeCompatibilityContractTest(unittest.TestCase):
    """Figma work defaults to the smallest evidence loop that fits."""

    def test_entry_has_targeted_strict_feature_and_slice_modes(self):
        skill = (ROOT / 'SKILL.md').read_text()

        for requirement in (
            'targeted-change',
            'strict-parity',
            'feature-delivery',
            'slice-implementation',
            'references/exact-node-workflow.md',
        ):
            self.assertIn(requirement, skill)

    def test_targeted_change_is_the_default_lightweight_entry(self):
        reference = (ROOT / 'references/exact-node-workflow.md').read_text()

        for requirement in (
            '`targeted-change`',
            'default',
            'exact Figma Design URL',
            '`node-id`',
            'current repository',
            'Feature Manifest is not required',
            'PRD is not required',
            'global Figma inventory is not required',
            'unambiguous repository evidence',
            'focused tests',
            'affected viewport',
        ):
            self.assertIn(requirement, reference)

        self.assertIn('No full visual-evidence manifest or receipt', reference)

    def test_strict_parity_preserves_the_existing_evidence_gate(self):
        reference = (ROOT / 'references/exact-node-workflow.md').read_text()

        for requirement in (
            '`strict-parity`',
            '逐帧',
            '逐像素',
            '每个距离',
            'visual-evidence.json',
            'RGBA',
            'viewport matrix',
            'validation-receipt.json',
            '`exact-node-implementation`',
        ):
            self.assertIn(requirement, reference)

    def test_node_work_escalates_only_when_scope_becomes_a_feature(self):
        reference = (ROOT / 'references/exact-node-workflow.md').read_text()

        for requirement in (
            'multiple routes',
            'product-owned states',
            '`feature-delivery`',
            'reuse existing exact-node evidence',
            'Do not invent',
            'API',
        ):
            self.assertIn(requirement, reference)

    def test_readme_explains_the_three_main_entries(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        for requirement in (
            '`targeted-change`',
            '`strict-parity`',
            '`feature-delivery`',
            '默认',
            '逐帧',
        ):
            self.assertIn(requirement, readme)

    def test_default_prompt_discovers_all_entry_shapes(self):
        metadata = (ROOT / 'agents/openai.yaml').read_text()

        self.assertIn('targeted change', metadata)
        self.assertIn('strict visual parity', metadata)
        self.assertIn('full product feature', metadata)


if __name__ == '__main__':
    unittest.main()
