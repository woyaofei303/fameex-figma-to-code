from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillTokenEfficiencyContractTest(unittest.TestCase):
    def test_entry_skill_stays_compact_without_losing_conditional_routes(self):
        skill = (ROOT / 'SKILL.md').read_text()

        self.assertLessEqual(
            len(skill.split()),
            500,
            'Keep the always-loaded entry concise; move detail to references.',
        )
        for requirement in (
            '`targeted-change`',
            '`strict-parity`',
            'references/dependency-bootstrap.md',
            'references/existing-implementation-audit.md',
            'references/fameex-web.md',
            'references/api-integration.md',
            'references/verification-contract.md',
            'authenticated exact-node read',
            'For server-backed work only',
            'audit_reuse.py` only when',
            'reuse`, `adapt`, `promote`, or `local',
            'Simplified Chinese',
            '`figma-implement-design`',
            '`playwright`',
            '`superpowers:verification-before-completion`',
            'ask before any installation or configuration change',
        ):
            self.assertIn(requirement, skill)

        targeted = skill.split('- `targeted-change`', 1)[1].split(
            '- `strict-parity`', 1
        )[0]
        self.assertIn('No full visual manifest', targeted)

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

    def test_final_response_expands_only_for_strict_or_feature_work(self):
        contract = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'Targeted response',
            'Outcome',
            '修改文件',
            'Validation',
            'Failures and Deviations',
            '查看修改',
            'Strict or feature additions',
            'Figma Mapping',
            'Reuse Decisions',
            'Artifacts',
            'Pending Business Questions',
        ):
            self.assertIn(requirement, contract)

    def test_readme_is_a_concise_human_entry_not_a_second_skill(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        headings = (
            '## 这套 Skill 解决什么问题',
            '## 模式',
            '## 快速使用',
            '## 验证 Skill',
        )
        for heading in headings:
            self.assertIn(heading, readme)
        self.assertLess(readme.index(headings[0]), readme.index(headings[1]))
        self.assertLess(readme.index(headings[1]), readme.index(headings[2]))

        self.assertLessEqual(len(readme.splitlines()), 180)
        for requirement in (
            '找对页面',
            '看懂设计',
            '不替业务做决定',
            '用真实结果验收',
            '安装或修改配置前',
        ):
            self.assertIn(requirement, readme)

        self.assertNotIn('flowchart TD', readme)


if __name__ == '__main__':
    unittest.main()
