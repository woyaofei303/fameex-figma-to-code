from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FameexWebLocalizationContractTest(unittest.TestCase):
    def test_customer_web_metadata_uses_tdk_namespace(self):
        rules = (ROOT / 'references/fameex-web.md').read_text()

        for requirement in (
            'Customer Web page-level metadata belongs to the dedicated `tdk` namespace',
            "const { t } = await getT(lang, 'tdk')",
            'tdk:<route-key>.title',
            'tdk:<route-key>.description',
            'tdk:<route-key>.keyWords',
            'Do not add a `meta` subtree to a feature namespace',
            'Body copy remains in the owning feature namespace',
            'Backend-owned dynamic SEO remains backend-owned',
            'ZH_CN_SOURCE_ONLY_TDK_KEYS',
            'shared `tdk`',
            'focused loader test',
            '--allow-unused',
        ):
            self.assertIn(requirement, rules)

    def test_repository_rules_are_portable_and_keep_legacy_language(self):
        rules = (ROOT / 'references/fameex-web.md').read_text()

        self.assertNotIn('/Users/julian/fameex-web', rules)
        self.assertIn('Repository: `<repo-root>`', rules)
        self.assertIn('hooks remain in the owning app', rules)
        self.assertIn('preserve its existing JavaScript', rules)

    def test_readme_explains_tdk_ownership(self):
        readme_path = ROOT / 'README.md'
        if not readme_path.exists():
            self.skipTest('installed runtime bundle does not include README.md')
        readme = readme_path.read_text()

        self.assertIn('Customer Web 的页面级 Meta 文案统一放在 `tdk`', readme)


if __name__ == '__main__':
    unittest.main()
