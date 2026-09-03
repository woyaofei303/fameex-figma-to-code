from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VisualFidelityLoopContractTest(unittest.TestCase):
    def test_entry_routes_visual_work_to_the_fidelity_loop(self):
        skill = (ROOT / 'SKILL.md').read_text()

        self.assertIn('references/visual-fidelity-loop.md', skill)
        self.assertIn('one section, one state, and one viewport', skill)

    def test_loop_has_an_evidence_gate_and_a_bounded_stop_rule(self):
        reference_path = ROOT / 'references/visual-fidelity-loop.md'
        self.assertTrue(reference_path.exists())
        reference = reference_path.read_text()

        for requirement in (
            'Evidence Gate',
            'asset/effect inventory',
            'one section, one state, and one viewport',
            'high-salience mismatch',
            'Do not advance',
        ):
            self.assertIn(requirement, reference)

    def test_geometry_ledger_distinguishes_responsive_sizing_semantics(self):
        reference = (ROOT / 'references/visual-fidelity-loop.md').read_text()

        for requirement in (
            '`fixed`',
            '`fluid`',
            '`intrinsic`',
            '`anchored`',
            '`scroll`',
            '`clipped`',
            'exact `gap`',
            '`justify-between`',
            'parent is adaptive',
            'flex-basis',
            'flex-grow',
            'flex-shrink',
            'min/max-width',
            'bounding rect',
            'responsive fit failure',
        ):
            self.assertIn(requirement, reference)

    def test_viewport_matrix_checks_width_height_tables_and_motion(self):
        reference = (ROOT / 'references/visual-fidelity-loop.md').read_text()

        for requirement in (
            'breakpoint - 1',
            'breakpoint',
            'short viewport height',
            'pair that height with the minimum and maximum width of each responsive interval',
            'disjoint viewport captures',
            'window.innerWidth',
            'document.documentElement.clientWidth',
            '`th`',
            '`td`',
            'column start',
            'column center',
            'scrollWidth',
            'clientWidth',
            'IntersectionObserver',
            'actual scroll root',
            '`root`',
            '`rootMargin`',
            '`threshold`',
            'initially visible',
            'downward',
            'upward',
            'exit',
            're-entry',
            'responsive root change',
            '`unobserve`',
            '`disconnect`',
            '`reentry_policy`',
            '`reentry_verified`',
            '`once`',
            '`repeat`',
            'opacity',
            'transform',
            'unmount',
            'fail open',
        ):
            self.assertIn(requirement, reference)

    def test_state_visuals_assets_and_entry_points_have_explicit_contracts(self):
        reference = (ROOT / 'references/visual-fidelity-loop.md').read_text()

        for requirement in (
            'state × viewport',
            'single state source',
            'highlighted connector',
            'canonical ordered-progress model',
            'first, middle, final',
            'both responsive branches',
            'preserve SVG',
            'WebP',
            'alpha',
            'before/after bytes',
            'visual difference',
            'per-pixel alpha/RGBA difference',
            'alpha bounds alone are insufficient',
            'encoder/settings',
            'accepted or rejected',
            'one-time activity',
            'canonical page route',
            'operational exposure entry',
            'App WebView/deep link',
            'page-level CTA',
            'owner, evidence source, configuration location, status, and acceptance evidence',
            'Route existence does not prove',
            'must not infer',
        ):
            self.assertIn(requirement, reference)

    def test_validation_classifies_baseline_failures_without_overclaiming(self):
        reference = (ROOT / 'references/visual-fidelity-loop.md').read_text()

        for requirement in (
            'merge base',
            'before/after',
            '`introduced`',
            '`pre-existing`',
            '`environmental`',
            'focused tests',
            'real-route evidence',
        ):
            self.assertIn(requirement, reference)

    def test_completion_gate_requires_a_fresh_receipt_and_real_rgba(self):
        reference = (ROOT / 'references/visual-fidelity-loop.md').read_text()

        for requirement in (
            'compare_assets_rgba.py',
            '`lossless-exact`',
            '`--write-receipt`',
            '`validation-receipt.json`',
            'Git HEAD',
            'target files',
            'artifact hashes',
            'tracked diff',
            'untracked files',
            'validator/tool',
            'build hashes',
            '`--draft`',
        ):
            self.assertIn(requirement, reference)


if __name__ == '__main__':
    unittest.main()
