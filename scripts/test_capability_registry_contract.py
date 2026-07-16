from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CapabilityRegistryContractTest(unittest.TestCase):
    def test_entry_loads_compact_index_and_resumes_original_task(self):
        skill = (ROOT / 'SKILL.md').read_text()
        preflight = skill.split('## Workflow', 1)[0]

        for requirement in (
            'references/capability-index.md',
            'required or triggered',
            'resume the original task',
        ):
            self.assertIn(requirement, preflight)

        index = (ROOT / 'references/capability-index.md').read_text()
        self.assertIn('references/capability-registry.md', index)

    def test_registry_classifies_skills_plugins_mcp_and_apps(self):
        registry = (ROOT / 'references/capability-registry.md').read_text()

        for requirement in (
            'Required',
            'Conditional',
            'Optional',
            'Not used by default',
            '`figma`',
            '`figma-implement-design`',
            '`playwright`',
            '`superpowers:verification-before-completion`',
            '`verification-before-completion`',
            '`skill-installer`',
            '`lark-doc`',
            '`figma:figma-code-connect`',
            '`github:yeet`',
            '`figma@openai-curated`',
            '`superpowers@openai-curated`',
            'No App or Connector is mandatory',
            '`browser` / `chrome` / `computer-use`',
            '`imagegen`',
            'web search',
        ):
            self.assertIn(requirement, registry)

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

    def test_registry_installs_only_missing_triggered_capabilities_then_resumes(self):
        registry = (ROOT / 'references/capability-registry.md').read_text()

        for requirement in (
            'codex plugin list',
            'codex plugin add figma@openai-curated',
            'codex plugin add superpowers@openai-curated',
            '`skill-installer`',
            'scripts/bootstrap_dependencies.py',
            'npx skills add larksuite/cli -g -y',
            'codex mcp add figmaremotemcp --url https://mcp.figma.com/mcp',
            'codex mcp login figmaremotemcp',
            'Read the installed `SKILL.md`',
            'restart Codex or open a new task',
            'resume the original task',
            'Do not install optional or unrelated capabilities',
        ):
            self.assertIn(requirement, registry)

    def test_readme_explains_the_complete_capability_inventory(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        for requirement in (
            '## Skill、插件、MCP 和应用清单',
            '### 必需能力',
            '### 条件使用和可选能力',
            '### Figma MCP 实际使用的功能',
            '### 缺失时怎么补齐并继续',
            '### 默认不会使用',
            'figma@openai-curated',
            'superpowers@openai-curated',
            'lark-doc',
            'Code Connect',
            '没有必须安装的 App 或 Connector',
        ):
            self.assertIn(requirement, readme)


if __name__ == '__main__':
    unittest.main()
