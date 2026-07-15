from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillTokenEfficiencyContractTest(unittest.TestCase):
    def test_entry_skill_stays_compact_without_losing_phase_routes(self):
        skill = (ROOT / 'SKILL.md').read_text()

        self.assertLessEqual(
            len(skill.split()),
            500,
            'Keep the always-loaded entry concise; move detail to references.',
        )
        for requirement in (
            'references/dependency-bootstrap.md',
            'references/existing-implementation-audit.md',
            'references/fameex-web.md',
            'references/api-integration.md',
            'references/verification-contract.md',
            'authenticated exact-node read',
            'contract manifest',
            'audit_reuse.py',
            'reuse`, `adapt`, `promote`, or `local',
            'Simplified Chinese',
            '`figma-implement-design`',
            '`playwright`',
            '`superpowers:verification-before-completion`',
        ):
            self.assertIn(requirement, skill)

    def test_readme_describes_contract_tests_without_overclaiming_runtime_coverage(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        self.assertIn('静态合同检查', readme)
        self.assertIn('不能代替真实 MCP、仓库和浏览器验证', readme)

    def test_readme_avoids_volatile_pass_counts(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        self.assertIsNone(
            re.search(r'(?i)(skill|vip|vipgift)[^\n]{0,100}\b\d+/\d+\b', readme),
        )
        self.assertIn('验证数字以命令的当前输出为准', readme)


if __name__ == '__main__':
    unittest.main()
