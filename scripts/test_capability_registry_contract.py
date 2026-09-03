from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CapabilityRegistryContractTest(unittest.TestCase):
    def test_entry_loads_compact_index_and_repairs_only_triggered_capabilities(self):
        skill = (ROOT / 'SKILL.md').read_text()
        preflight = skill.split('## Workflow', 1)[0]

        self.assertIn('references/capability-index.md', preflight)
        self.assertIn('only capabilities triggered by the selected mode', preflight)
        self.assertIn('resume the original task', skill)

        index = (ROOT / 'references/capability-index.md').read_text()
        self.assertIn('references/capability-registry.md', index)

    def test_registry_classifies_mode_required_conditional_and_optional_tools(self):
        registry = (ROOT / 'references/capability-registry.md').read_text()

        for requirement in (
            'Mode-required',
            'Conditional',
            'Optional',
            'Not used by default',
            '`figma`',
            '`figma-implement-design`',
            '`playwright`',
            '`superpowers:verification-before-completion`',
            '`skill-installer`',
            '`lark-doc`',
            '`figma:figma-code-connect`',
            'No App or Connector is mandatory',
            '`browser` / `chrome` / `computer-use`',
            '`imagegen`',
            'web search',
        ):
            self.assertIn(requirement, registry)

    def test_engineering_capabilities_use_one_canonical_provider(self):
        index = (ROOT / 'references/capability-index.md').read_text()
        registry = (ROOT / 'references/capability-registry.md').read_text()

        for content in (index, registry):
            for requirement in ('`tdd`', '`diagnose`', '`review`'):
                self.assertIn(requirement, content)
            for outdated in (
                '`superpowers:test-driven-development`',
                '`diagnosing-bugs`',
                '`superpowers:systematic-debugging`',
                '`code-review`',
                '`github:yeet`',
            ):
                self.assertNotIn(outdated, content)

    def test_registry_lists_figma_mcp_functions_and_write_boundaries(self):
        registry = (ROOT / 'references/capability-registry.md').read_text()

        for requirement in (
            '`whoami`',
            '`get_design_context`',
            '`get_screenshot`',
            '`get_metadata`',
            '`get_variable_defs`',
            'asset URLs',
            '`get_code_connect_map`',
            '`get_code_connect_suggestions`',
            '`get_context_for_code_connect`',
            '`add_code_connect_map`',
            '`get_figjam`',
            '`create_design_system_rules`',
            '`get_strategy_for_mapping`',
            '`send_get_strategy_response`',
            'explicit user request',
        ):
            self.assertIn(requirement, registry)

    def test_recovery_requires_authorization_then_resumes_the_original_task(self):
        registry = (ROOT / 'references/capability-registry.md').read_text()

        for requirement in (
            'ask for user approval',
            'before installing',
            'codex plugin list',
            'codex plugin add figma@openai-curated',
            '`skill-installer`',
            'scripts/bootstrap_dependencies.py',
            'codex mcp add figmaremotemcp --url https://mcp.figma.com/mcp',
            'codex mcp login figmaremotemcp',
            'Read the installed `SKILL.md`',
            'restart Codex or open a new task',
            'resume the original task',
            'Do not install optional or unrelated capabilities',
        ):
            self.assertIn(requirement, registry)

    def test_readme_points_to_the_registry_without_copying_the_inventory(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        self.assertIn('references/capability-index.md', readme)
        self.assertIn('references/capability-registry.md', readme)
        self.assertIn('安装或修改配置前', readme)
        self.assertNotIn('## Skill、插件、MCP 和应用清单', readme)


if __name__ == '__main__':
    unittest.main()
