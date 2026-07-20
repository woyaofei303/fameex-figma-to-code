from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FameExWebDesignTokenContractTest(unittest.TestCase):
    def test_repository_reference_requires_project_token_discovery(self):
        reference = (ROOT / 'references/fameex-web.md').read_text()

        for requirement in (
            'packages/config/tailwind-preset.js',
            'apps/web/tailwind.config.js',
            'packages/ui/tailwind.config.js',
            'packages/utils/classNames.ts',
            'Style Uncertainty Protocol',
            'Follow imports recursively',
            'style ledger',
            'Figma node/property/value',
            'Do not assume Tailwind default utility values',
            '`rounded-m` = `8px`',
            '`rounded-lg` = `16px`',
            '`xl` = `1440px`',
            'maximum-width aliases',
            '`<md:text-[12px]`',
            '`max-sm:` or `max-md:`',
            'DOM class with no matching rule',
            'computed style',
        ):
            self.assertIn(requirement, reference)

    def test_exact_node_reference_requires_asset_first_and_state_matrix_work(self):
        reference = (ROOT / 'references/exact-node-workflow.md').read_text()

        for requirement in (
            'asset inventory',
            'before editing layout code',
            'At the start of every new exact route, state, or support-frame intake',
            'icon/image pass',
            'searchable pending marker',
            'state matrix',
            'Do not merge state-specific content',
            'same-node screenshots',
            'placeholder',
        ):
            self.assertIn(requirement, reference)

    def test_asset_failure_policy_is_consistent_across_figma_capabilities(self):
        registry = (ROOT / 'references/capability-registry.md').read_text()
        fallback = (ROOT / 'assets/fallback-skills/figma/SKILL.md').read_text()

        for document in (registry, fallback):
            self.assertIn('temporary placeholder', document)
            self.assertIn('user permits', document)
            self.assertIn('exact visual completion', document)

    def test_large_canvas_asset_and_historical_reuse_failures_are_guarded(self):
        reference = (ROOT / 'references/exact-node-workflow.md').read_text()

        for requirement in (
            'large canvas',
            '`get_metadata`',
            'child frames',
            'section geometry ledger',
            'route-shell offsets',
            'support frames',
            'download expiring asset URLs immediately',
            'every visible non-text visual',
            'user-supplied replacement asset',
            'interaction timeline',
            'historical implementation',
            'visual and interaction shell',
            'domain APIs',
        ):
            self.assertIn(requirement, reference)

    def test_responsive_branches_cannot_diverge_or_crop_between_breakpoints(self):
        reference = (ROOT / 'references/fameex-web.md').read_text()

        for requirement in (
            'activation breakpoint',
            'fixed-width desktop',
            'intermediate widths',
            'responsive branches',
            'same business state',
        ):
            self.assertIn(requirement, reference)

    def test_browser_contract_checks_computed_styles_and_cta_truthfulness(self):
        reference = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'computed styles',
            'section crops',
            'overlay/difference',
            'asset inventory',
            'pending placeholder',
            'breakpoint boundaries',
            'disabled appearance',
            'handler behavior',
            'cross-breakpoint',
        ):
            self.assertIn(requirement, reference)

    def test_motion_and_reference_reuse_require_behavioral_regression_evidence(self):
        exact_node = (ROOT / 'references/exact-node-workflow.md').read_text()
        verification = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'user-named reference',
            'trigger lock',
            'traversal order',
            'loop count',
            'legacy-consumer behavior',
            'sample users',
        ):
            self.assertIn(requirement, exact_node)

        for requirement in (
            'active-index sequences',
            'immediate input lock',
            'duplicate-click prevention',
            'cleanup on unmount',
            'historical consumer',
        ):
            self.assertIn(requirement, verification)

    def test_business_and_visual_authority_are_kept_separate(self):
        reference = (ROOT / 'references/fameex-web.md').read_text()

        for requirement in (
            'PRD/backend/user corrections own business rules',
            'exact Figma nodes own visual structure',
            'not production constants',
            'historical ranking, lottery, tab, FAQ disclosure, or share',
        ):
            self.assertIn(requirement, reference)

    def test_typography_display_config_and_route_shell_pitfalls_are_documented(self):
        reference = (ROOT / 'references/fameex-web.md').read_text()

        for requirement in (
            '`text-h4` = `20px / 30px`',
            '`text-body-regular` = `14px / 21px`',
            '`text-body-s` = `12px / 18px`',
            '`text-xl` / `text-sm` / `text-xs`',
            'display configuration',
            'numeric target',
            'feature-flag',
            'duplicate Header or Footer',
        ):
            self.assertIn(requirement, reference)

    def test_browser_interaction_evidence_requires_a_hydrated_client(self):
        reference = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'client hydration',
            'material state change',
            'DOM-only screenshot',
            'canonical local host',
            'HMR',
        ):
            self.assertIn(requirement, reference)

    def test_one_time_activity_has_a_standalone_removal_boundary(self):
        repository = (ROOT / 'references/fameex-web.md').read_text()
        verification = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'One-Time Activity Isolation',
            'generic Campaign renderer',
            '`apps/web/src/apps/Marketing/<Feature>/`',
            '`apps/web/public/static/marketing/<slug>/`',
            'removal ledger',
            'route slug and feature name',
            'cross-cutting shell hooks',
            'production query parameter',
        ):
            self.assertIn(requirement, repository)

        for requirement in (
            'one-time standalone activity',
            'removal ledger',
            'explicit deletion boundary',
            'generic Campaign renderer',
        ):
            self.assertIn(requirement, verification)

    def test_uncertain_styles_resolve_active_config_and_merged_output(self):
        reference = (ROOT / 'references/fameex-web.md').read_text()

        for requirement in (
            'active app config',
            'inherited preset',
            'component variants',
            'merged class string',
            'Figma `8px` radius',
            '`rounded-m`',
            'Figma `16px` radius',
            '`rounded-lg`',
        ):
            self.assertIn(requirement, reference)

    def test_visual_comparison_does_not_confuse_scrollbars_with_product_css(self):
        verification = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'window.innerWidth',
            'document.documentElement.clientWidth',
            'browser scrollbar',
            'test-only capture',
            'production CSS',
            'full-page dimensions',
            'does not establish pixel parity',
            'section-local coordinates',
        ):
            self.assertIn(requirement, verification)

    def test_visual_difference_triage_covers_assets_type_and_state(self):
        verification = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'object-fit',
            'object-position',
            'alpha bounds',
            'typography baseline',
            'content/state difference',
            'asset mismatch',
            'crop/scale mismatch',
        ):
            self.assertIn(requirement, verification)

    def test_exact_node_asset_intake_preserves_transparency_and_mask_semantics(self):
        workflow = (ROOT / 'references/exact-node-workflow.md').read_text()

        for requirement in (
            'SVG viewBox',
            'asset hash',
            'transparent cutouts',
            'parent background',
            'alpha channel',
            'mask source',
            'direct overlay',
            'object-fit',
            'object-position',
        ):
            self.assertIn(requirement, workflow)

    def test_pixel_comparison_does_not_hardcode_figma_sample_values(self):
        verification = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'sample balance',
            'sample ranking',
            'sample countdown',
            'backend or deterministic acceptance-state value',
            'do not hardcode',
        ):
            self.assertIn(requirement, verification)

    def test_visual_layer_inventory_covers_background_composition_and_user_slots(self):
        workflow = (ROOT / 'references/exact-node-workflow.md').read_text()
        verification = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'visual-layer inventory',
            'named slot',
            'intrinsic/viewBox',
            'rendered width/height',
            'background image',
            'background-size',
            'background-position',
            'filter/blur',
            'mix-blend-mode',
            'opacity',
            'z-index',
        ):
            self.assertIn(requirement, workflow)

        for requirement in (
            'background stack',
            'glow',
            'blur',
            'blend mode',
            'layer order',
        ):
            self.assertIn(requirement, verification)

    def test_every_reference_route_and_exact_frame_has_independent_evidence(self):
        workflow = (ROOT / 'references/exact-node-workflow.md').read_text()
        verification = (ROOT / 'references/verification-contract.md').read_text()

        for requirement in (
            'reference route/source map',
            'historical route',
            'source component',
            'source asset',
            'Desktop/H5',
            'frame evidence matrix',
            'one row per exact frame',
        ):
            self.assertIn(requirement, workflow)

        for requirement in (
            'frame evidence matrix',
            'structured context',
            'same-node screenshot',
            'asset inventory',
            'style ledger',
            'actual crop',
            'overlay/difference',
            'unexplained high-salience',
        ):
            self.assertIn(requirement, verification)


if __name__ == '__main__':
    unittest.main()
