from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProductDeliveryWorkflowContractTest(unittest.TestCase):
    def test_entry_routes_feature_slice_and_existing_audit_modes(self):
        skill = (ROOT / 'SKILL.md').read_text()

        for requirement in (
            'feature-delivery',
            'slice-implementation',
            'audit-existing',
            'references/product-delivery-workflow.md',
        ):
            self.assertIn(requirement, skill)

    def test_feature_workflow_connects_product_design_code_api_and_acceptance(self):
        workflow = (ROOT / 'references/product-delivery-workflow.md').read_text()

        for requirement in (
            'embedded Sheet',
            'linked document',
            'global Figma root',
            'exact implementation node',
            'Feature Manifest',
            'business slice',
            'Traceability',
            'not-required',
            'waiting',
            'documented',
            'integrated',
            'verified',
            'Admin before Web',
            'missing permission',
            'production fallback',
            'acceptance',
        ):
            self.assertIn(requirement, workflow)

    def test_optional_decision_skills_have_narrow_non_overlapping_triggers(self):
        workflow = (ROOT / 'references/product-delivery-workflow.md').read_text()
        registry = (ROOT / 'references/capability-registry.md').read_text()

        for requirement in (
            '`grill-me`',
            '`grill-with-docs`',
            '`prototype`',
            'one interview mode',
            'CONTEXT.md',
            'logic prototype',
            'UI prototype',
            'delete or absorb',
            'Do not load',
        ):
            self.assertIn(requirement, workflow)

        for requirement in ('`grill-me`', '`grill-with-docs`', '`prototype`'):
            self.assertIn(requirement, registry)

    def test_feature_manifest_template_keeps_evidence_and_slice_status(self):
        template = (ROOT / 'assets/templates/feature-manifest.yaml').read_text()

        for requirement in (
            'product_sources:',
            'figma_sources:',
            'conflicts:',
            'slices:',
            'requirements:',
            'figma_nodes:',
            'api_status:',
            'test_seams:',
            'acceptance:',
            'evidence:',
            'blockers:',
        ):
            self.assertIn(requirement, template)

        workflow = (ROOT / 'references/product-delivery-workflow.md').read_text()
        self.assertIn('test seam', workflow)

    def test_readme_explains_feature_intake_concisely(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        for requirement in (
            '`feature-delivery`',
            '完整需求和 Figma 总入口',
            '按业务切片开发',
            'references/product-delivery-workflow.md',
        ):
            self.assertIn(requirement, readme)


if __name__ == '__main__':
    unittest.main()
