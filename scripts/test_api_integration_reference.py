from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ApiIntegrationReferenceTest(unittest.TestCase):
    def test_skill_loads_api_reference_only_for_server_backed_work(self):
        skill = (ROOT / 'SKILL.md').read_text()

        self.assertIn('references/api-integration.md', skill)
        self.assertIn('server-backed', skill)
        self.assertIn('contract manifest', skill)
        self.assertIn('each interaction or independently releasable slice', skill)

    def test_contract_gate_does_not_block_independent_slices(self):
        reference = (ROOT / 'references/api-integration.md').read_text()

        self.assertIn('before editing that interaction or slice', reference)
        self.assertIn('must not block a confirmed independent slice', reference)

    def test_admin_filter_width_rule_is_in_always_loaded_repository_rules(self):
        rules = (ROOT / 'references/fameex-web.md').read_text()

        self.assertIn("owning Admin page's field/control width pattern", rules)
        self.assertIn('sibling tabs', rules)

    def test_reference_defines_reusable_contract_manifest(self):
        reference = (ROOT / 'references/api-integration.md').read_text()

        for field in (
            'consumer_app',
            'source_of_truth',
            'endpoint',
            'method',
            'auth_scope',
            'request_query_or_body',
            'response_fields',
            'inbound_normalization',
            'outbound_normalization',
            'query_key',
            'enabled_condition',
            'mutation_refresh',
            'verification',
        ):
            self.assertIn(field, reference)

    def test_validation_matrix_uses_owning_package_commands(self):
        rules = (ROOT / 'references/fameex-web.md').read_text()

        self.assertIn(
            'pnpm --filter @fameex/admin exec vitest --run --cache=false',
            rules,
        )
        self.assertIn(
            'pnpm vitest --run --cache=false <web-target-tests...>',
            rules,
        )
        self.assertIn('node --check <legacy-admin-files...>', rules)

    def test_browser_contract_requires_network_and_state_evidence(self):
        contract = (ROOT / 'references/verification-contract.md').read_text()

        for evidence in (
            'method, path, query, and body',
            'loading, error, empty, and disabled',
            'invalidation or refetch',
            'inactive tab',
        ):
            self.assertIn(evidence, contract)

    def test_readme_lists_optional_api_reference(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        self.assertIn('references/api-integration.md', readme)


if __name__ == '__main__':
    unittest.main()
