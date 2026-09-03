from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FigmaMcpBootstrapContractTest(unittest.TestCase):
    def test_entry_repairs_triggered_runtime_tools_only_after_approval(self):
        skill = (ROOT / 'SKILL.md').read_text()

        self.assertIn('If a triggered capability is absent', skill)
        self.assertIn('ask before any installation or configuration change', skill)
        self.assertIn('references/dependency-bootstrap.md', skill)

    def test_main_skill_separates_skill_discovery_from_mcp_availability(self):
        skill = (ROOT / 'SKILL.md').read_text()

        for requirement in (
            'A `figma` skill, MCP registration, or OAuth alone is insufficient',
            'authenticated exact-node read',
            'current task',
        ):
            self.assertIn(requirement, skill)

    def test_dependency_reference_registers_and_authenticates_official_mcp(self):
        reference = (ROOT / 'references/dependency-bootstrap.md').read_text()

        for requirement in (
            'https://mcp.figma.com/mcp',
            'codex mcp add figmaremotemcp --url https://mcp.figma.com/mcp',
            'codex mcp login figmaremotemcp',
            'codex mcp list',
            'OAuth is interactive',
            'whoami',
            'user approval',
        ):
            self.assertIn(requirement, reference)

    def test_dependency_reference_selects_by_capability_not_alias(self):
        reference = (ROOT / 'references/dependency-bootstrap.md').read_text()

        for requirement in (
            'server alias',
            'authenticated entry',
            'Not logged in',
            'same selected server',
        ):
            self.assertIn(requirement, reference)

    def test_dependency_reference_requires_runtime_refresh_when_tools_are_absent(self):
        reference = (ROOT / 'references/dependency-bootstrap.md').read_text()

        for requirement in (
            'registration or OAuth success does not prove',
            'restart Codex or open a new task',
            'Visual work remains blocked',
        ):
            self.assertIn(requirement, reference)

    def test_visual_blocker_does_not_block_independent_non_visual_fixes(self):
        dependency = (ROOT / 'references/dependency-bootstrap.md').read_text()
        audit = (ROOT / 'references/existing-implementation-audit.md').read_text()

        for content in (dependency.lower(), audit.lower()):
            self.assertIn('visual work remains blocked', content)
            self.assertIn('independently evidenced non-visual', content)

    def test_fallback_figma_skill_includes_oauth_first_config_reference(self):
        fallback_skill = (ROOT / 'assets/fallback-skills/figma/SKILL.md').read_text()
        config = (
            ROOT
            / 'assets/fallback-skills/figma/references/figma-mcp-config.md'
        ).read_text()

        self.assertIn('references/figma-mcp-config.md', fallback_skill)
        self.assertIn('codex mcp login figmaremotemcp', config)
        self.assertIn('preferred OAuth flow', config)
        self.assertIn('Optional bearer-token fallback', config)
        self.assertIn('Do not print', config)

    def test_readme_explains_user_action_and_restart_boundary(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        for requirement in (
            'codex mcp login figmaremotemcp',
            'OAuth 授权需要用户确认',
            '重启 Codex 或新建任务',
        ):
            self.assertIn(requirement, readme)


if __name__ == '__main__':
    unittest.main()
