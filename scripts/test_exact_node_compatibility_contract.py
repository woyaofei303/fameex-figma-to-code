from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ExactNodeCompatibilityContractTest(unittest.TestCase):
    """The previous entry described exact node-id work but exposed no mode
    that could start without a Feature Manifest.
    """

    def test_entry_has_distinct_exact_node_feature_and_slice_modes(self):
        skill = (ROOT / 'SKILL.md').read_text()

        for requirement in (
            'exact-node-implementation',
            'feature-delivery',
            'slice-implementation',
            'references/exact-node-workflow.md',
        ):
            self.assertIn(requirement, skill)

    def test_exact_node_mode_keeps_the_original_lightweight_entry(self):
        reference = (ROOT / 'references/exact-node-workflow.md').read_text()

        for requirement in (
            'exact Figma Design URL',
            '`node-id`',
            'current repository',
            'Feature Manifest is not required',
            'PRD is not required',
            'global Figma inventory is not required',
            'unambiguous repository evidence',
            'focused tests',
            'real-route evidence',
        ):
            self.assertIn(requirement, reference)

    def test_exact_node_mode_escalates_only_when_scope_becomes_a_feature(self):
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

    def test_readme_explains_both_compatible_entries(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        for requirement in (
            '两种入口可以同时使用',
            '精确节点直达',
            '不需要先创建 Feature Manifest',
            '完整需求模式',
            '带 node-id 的 Figma Design 链接',
        ):
            self.assertIn(requirement, readme)

    def test_default_prompt_discovers_both_entry_shapes(self):
        metadata = (ROOT / 'agents/openai.yaml').read_text()

        self.assertIn('exact-node page', metadata)
        self.assertIn('full product feature', metadata)


if __name__ == '__main__':
    unittest.main()
