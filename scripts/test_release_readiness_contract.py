from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseReadinessContractTest(unittest.TestCase):
    """Baseline pressure omitted cross-slice regression, review, build/CI,
    sign-offs, concrete rollback, and post-release proof before saying ready.
    """

    def test_entry_routes_release_and_post_release_modes(self):
        skill = (ROOT / 'SKILL.md').read_text()

        for requirement in (
            'release-readiness',
            'post-release-validation',
            'references/release-readiness.md',
            'references/capability-index.md',
        ):
            self.assertIn(requirement, skill)

    def test_default_capability_read_is_compact_and_heavy_registry_is_conditional(self):
        skill = (ROOT / 'SKILL.md').read_text()
        index = (ROOT / 'references/capability-index.md').read_text()

        self.assertLessEqual(len(index.split()), 220)
        self.assertIn('references/capability-registry.md', index)
        self.assertIn('missing or triggered', index)
        self.assertIn('references/capability-index.md', skill)
        self.assertNotIn(
            '[references/capability-registry.md]',
            skill.split('## Workflow', 1)[0],
        )

    def test_release_reference_has_real_entry_exit_and_rollback_gates(self):
        release = (ROOT / 'references/release-readiness.md').read_text().lower()
        registry = (ROOT / 'references/capability-registry.md').read_text()

        for requirement in (
            'fixed release commit',
            'cross-slice regression',
            'standards axis',
            'spec axis',
            'target-environment build',
            'ci status',
            'product sign-off',
            'design sign-off',
            'backend sign-off',
            'qa sign-off',
            'release window',
            'rollback trigger',
            'rollback action',
            'monitoring owner',
            'production-safe smoke',
            'post-release evidence',
            'explicit user authorization',
            'existing deployment pipeline',
            'ready-with-known-risks',
            'rolled-back',
        ):
            self.assertIn(requirement, release)

        self.assertIn('assets/templates/release-readiness.yaml', release)
        self.assertIn('`review`', registry)

    def test_feature_manifest_traces_each_requirement_and_local_history(self):
        workflow = (ROOT / 'references/product-delivery-workflow.md').read_text()
        manifest = (ROOT / 'assets/templates/feature-manifest.yaml').read_text()

        for requirement in (
            'local history',
            'exact ticket',
            'current repository',
            'development',
            'integration',
            'regression',
            'release',
        ):
            self.assertIn(requirement, workflow)

        for requirement in (
            'history_sources:',
            'traceability:',
            'requirement_id:',
            'requirement_status:',
            'analytics:',
            'development_status:',
            'integration_status:',
            'regression_status:',
            'release_status:',
        ):
            self.assertIn(requirement, manifest)

    def test_release_template_records_review_regression_and_operations(self):
        template = (ROOT / 'assets/templates/release-readiness.yaml').read_text()

        for requirement in (
            'release_commit:',
            'slice_gate:',
            'review:',
            'standards_axis:',
            'spec_axis:',
            'regression_matrix:',
            'build_and_ci:',
            'build_evidence:',
            'ci_provider:',
            'ci_reference:',
            'sign_offs:',
            'rollout:',
            'deployment_authorization:',
            'authorized_by:',
            'authorized_scope:',
            'rollback:',
            'monitoring:',
            'post_release:',
            'final_status:',
        ):
            self.assertIn(requirement, template)

    def test_completion_contract_separates_slice_feature_and_release_claims(self):
        verification = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'Slice verified',
            'Feature regression verified',
            'Release ready',
            'Released and verified',
            'does not prove release readiness',
        ):
            self.assertIn(requirement, verification)

    def test_readme_explains_the_full_closed_loop_without_auto_deploying(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        for requirement in (
            '需求到上线的完整闭环',
            '联调完成不等于可以上线',
            '回归审查',
            '发布准入',
            '回滚方案',
            '上线后验证',
            '只实现不依赖接口的子切片',
            '明确授权',
        ):
            self.assertIn(requirement, readme)


if __name__ == '__main__':
    unittest.main()
