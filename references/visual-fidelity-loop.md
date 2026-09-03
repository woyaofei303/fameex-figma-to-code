# Visual Fidelity Loop

Load for visual implementation or visual audit after exact-node intake and
repository mapping. This reference makes the existing asset, style, state, and
browser contracts executable; it does not replace them.

## Operating Rule

Converge one section, one state, and one viewport at a time. Keep a row for the
exact frame/node, section, state, viewport, implementation crop, measurements,
overlay/difference evidence, and disposition. Do not advance while that row has
an unexplained high-salience mismatch in artwork, crop, geometry, typography,
state, or motion. Mark a missing source or runtime as blocked instead of
silently accepting an approximation.

## Evidence Gate

Complete the exact-node asset/effect inventory before editing the section. The
asset/effect inventory must cover foreground artwork, icons, masks, gradients,
glows, shadows, pseudo-elements, clipping, and responsive/state variants.
Reconcile each visible layer with an original asset, repository reuse,
authoritative user replacement, or an explicitly pending placeholder.

Use only the canonical manifest copied from
`assets/templates/visual-evidence.json` to
`output-tdd/figma-audits/<task>/visual-evidence.json`. Its rows replace
task-invented YAML ledgers or evidence formats. Supporting crops, measurements,
and differences remain separate files, but every artifact is referenced by the
canonical manifest.

All verified artifacts stay under that task audit directory. Populate
`required_viewports` from exact frames, repository breakpoints, and user
corrections; the validator must find a matching responsive row for each. In
each section sizing row, compare sourced `expected` intent, distribution, and
gap with measured `actual` values. A passing status cannot override different
values such as `gap` versus `justify-between` or `fluid` versus `fixed`.

Completion artifacts are typed evidence, not opaque files:

```text
structured context: JSON with source=figma-mcp, passed status, file_key, node_id
same-node screenshot, crop, difference, correction: valid PNG/JPEG/WebP
geometry and style: passed Playwright JSON for the matching section IDs
layer composition: passed Figma MCP or Playwright JSON naming the layer IDs
table: passed Playwright JSON matching columns, edges, scroll/client widths
motion: passed Playwright JSON matching kind, lifecycle, and observer fields
historical reuse and entry surfaces: passed source JSON naming the collection
```

JSON labels alone are not sufficient: the validator also reconciles their
identity and measured fields with the manifest and binds their hashes in the
receipt. Evidence generated outside the named source must remain pending.

Schema `1.x` manifests are historical drafts only. To migrate, copy the current
`2.0` template, fill `task.target_paths` and the expanded table, motion,
historical-reuse, and entry-surface fields, recapture typed artifacts, run
`--draft`, then generate a new receipt. Never copy a v1 verified status forward
or edit an old receipt into the new shape.

For the active row, record:

```text
exact node and screenshot
asset/effect inventory entries
style and geometry ledger entries
expected state and data source
actual section crop and measured values
overlay/difference result
open mismatch or pass evidence
```

An existing historical component is evidence for a reuse candidate, not for
the target geometry. Re-measure it in the new route, state, and viewport.

## Geometry and Sizing Ledger

For every changed flex/grid container and every direct child that controls the
result, classify the sizing or positioning intent as `fixed`, `fluid`,
`intrinsic`, `anchored`, `scroll`, or `clipped`. Record:

```text
width/height rule and min/max-width
flex-basis / flex-grow / flex-shrink or grid tracks
wrap, alignment, distribution, and exact gap
padding and first/last-child edge distance
overflow owner and intended scroll axis
breakpoint activation and measured bounding rect
```

The fact that a parent is adaptive does not imply that its children should
stretch, use equal tracks, or use `justify-between`. Preserve an exact `gap`,
intrinsic child width, fixed artwork size, or scroll lane when the design
establishes it. Resolve the final Tailwind/computed value through
`fameex-web.md`; never infer a numeric gap from the utility name.

Do not use `overflow: hidden/clip`, scale, compressed typography, or hidden
content to conceal a responsive fit failure. Clipping is valid only when the
exact frame or asset composition establishes a crop/mask. Otherwise prove each
critical child's bounding rect remains inside its intended container at every
matrix width.

For tables, rankings, or repeated-field layouts, record each column start,
width, and column center. Compare every `th` with representative `td` cells,
including the first/last row and content extremes such as long identifiers and
different numeric widths. Record first/last column edge distances plus
`scrollWidth` and `clientWidth`. A visually plausible first row or a
three-column declaration alone does not prove equal distribution or alignment.

## State × Viewport Contract

Create a state × viewport matrix from exact frames plus confirmed
business-reachable states. A correction to one component does not authorize
copying its dimensions, color, line thickness, or token to a sibling; each
component keeps its own exact-node evidence.

For an ordered ladder, milestone, or other monotonic progress UI,
define one canonical ordered-progress model. Derive the item state, highlighted connector
endpoint, glow/background, icon, copy color, accessibility state, and both responsive branches
from that single state source. Do not maintain independent index checks or percentages that
can disagree. Verify first, middle, final, and every confirmed terminal state; label a
combination without an exact frame as behavior evidence rather than exact-frame parity.

## Width × Height Viewport Matrix

Derive breakpoints from the active repository config. At minimum verify:

```text
every exact Figma viewport
user-declared minimum and maximum supported widths
breakpoint - 1 and breakpoint
one representative intermediate width per responsive interval
the width that reproduced a reported defect
exact design height and any user-declared short viewport height
```

When a user declares both a supported width range and a short viewport height, pair that height with the minimum and maximum width of each responsive interval.
Run the complete primary interaction at both endpoint pairs; do not satisfy the height
and width requirements with disjoint viewport captures. This is an endpoint contract,
not a requirement to test the full width × height Cartesian product.

At the short viewport height, run the complete primary interaction rather than
taking only a screenshot. Prove the correct page/modal scroll owner, close
control, fixed CTA, final action, safe-area clearance, and focused/keyboard
behavior are reachable. For intentional horizontal lanes, prove manual
left/right scrolling and preserve the designed visible extent.

The interaction artifact is JSON produced from the Playwright run and records
`source: playwright`, the exact width/height, passed status, and matching
trigger, scroll owner, close control, final action, safe-area, and horizontal
scroll steps. A screenshot or hand-set manifest booleans alone do not satisfy
this evidence.

Record `window.innerWidth` and
`document.documentElement.clientWidth` for every browser comparison. Do not
repair production CSS for a scrollbar or automation-only viewport difference.

## Visibility-Triggered Motion

For `IntersectionObserver` or any scroll reveal, record the actual scroll root
and overflow owner plus configured `root`, `rootMargin`, and `threshold`.
Verify:

```text
content initially visible in the viewport
downward and upward entry
exit and intended re-entry policy
responsive root change
computed opacity and transform before/during/after motion
`unobserve` and `disconnect` behavior on completion or unmount
reduced-motion and unsupported-observer behavior
```

Record `reentry_policy` as `once` or `repeat`, then record
`reentry_verified` separately. Verification booleans prove the behavior was
checked; they must not encode the behavior's configured value. Apply the same
`*_verified` naming to entry direction, exit, responsive-root, cleanup, and
fallback checks.

Content must fail open as visible when observer setup, hydration, or reduced
motion prevents the decoration from running. A reveal that succeeds only after
scrolling from the page top, or leaves content permanently transparent, fails.

## Asset Conversion Evidence

Default: preserve SVG as vector unless an authoritative delivery constraint requires
another format. Consider WebP for large raster assets only after the asset and
composition evidence is locked; do not batch-convert merely by extension.

For each candidate record:

```text
source and candidate path/hash
encoder/settings and lossless/lossy mode
intrinsic and rendered dimensions
alpha presence/bounds and transparent padding
before/after bytes and percentage saved
Desktop/H5 crop or visual difference evidence
accepted or rejected decision and reason
```

Do not trim transparent padding without composition evidence. Reject the
candidate when alpha, crop, typography inside artwork, or another high-salience
pixel changes. For transparency-bearing assets, inspect a per-pixel alpha/RGBA difference;
alpha bounds alone are insufficient because colors or interior opacity can change inside
unchanged bounds. Keep assets and locale ownership for a one-time activity inside its
removal boundary so optimization does not leak page-bound files into shared packages.

Use `scripts/audit_assets.py` to collect zero-dependency header metadata before
making a conversion decision. Its `alpha_encoding_signaled` field means only
that the container can encode alpha; it does not prove that decoded pixels are
transparent or unchanged.

Generate the comparison artifact from the real source and candidate files:

```bash
/usr/bin/python3 <skill-root>/scripts/compare_assets_rgba.py \
  --source <source-asset> \
  --candidate <candidate.webp> \
  --output output-tdd/figma-audits/<task>/asset-difference.json
```

Only the decoded-pixel `lossless-exact` policy can authorize `accepted`.
The comparator tries Pillow first and falls back to the macOS image decoder
when needed. The sips-only path requires an 8-bit decoded PNG; use a
WebP-capable Pillow decoder for 16-bit sources. When no backend can decode both
files, keep the candidate `unverified` or `rejected`. Byte savings, matching
dimensions, header metadata, and
hand-authored zero deltas are not visual proof. Source and candidate must exist
inside the repository. The validator decodes and compares them again, then
requires the task-scoped comparison JSON to match the actual hashes, dimensions,
pixel counts, RGBA deltas, alpha statistics, decoder, tool, and policy.

## User Correction Ledger

When the user reports a visual, layout, responsive, asset, state, or motion
defect, add a correction row with a bounded source locator and every affected
frame/section/viewport row. Fixing one screenshot does not close the correction.
Re-run the affected historical rows and attach fresh comparison evidence before
marking it closed.

## Entry Surface Manifest

Keep these surfaces separate:

```text
canonical page route
operational exposure entry (banner, activity center, menu, or campaign slot)
App WebView/deep link entry
page-level CTA or share destination
```

For each surface record:

```text
owner, evidence source, configuration location, status, and acceptance evidence
```

Route existence does not prove an exposure entry or deeplink. A Figma screen proves
presentation, not an operational placement. When PRD, repository, or App configuration
does not establish a surface, mark it unresolved and must not infer it from another row;
block only the dependent entry work.

## Validation and Closeout

Run focused tests and real-route evidence for the active row before widening the
scope. For package typecheck, lint, or build failures, compare merge base and
before/after results where practical, then classify every failure as
`introduced`, `pre-existing`, or `environmental`. A focused test passing does
not turn an unrelated failing typecheck into a pass.

Use `--draft` only while filling the schema; a draft pass is never completion
evidence:

```bash
/usr/bin/python3 <skill-root>/scripts/validate_visual_evidence.py \
  --manifest output-tdd/figma-audits/<task>/visual-evidence.json \
  --repo-root <repo> \
  --draft
```

Before a visual completion statement, `output-tdd/` must be ignored by Git and
the manifest must list explicit `target_paths`. Freeze the intended worktree
snapshot, then use `--write-receipt` to generate and immediately recheck the
canonical receipt:

```bash
/usr/bin/python3 <skill-root>/scripts/validate_visual_evidence.py \
  --manifest output-tdd/figma-audits/<task>/visual-evidence.json \
  --repo-root <repo> \
  --write-receipt

/usr/bin/python3 <skill-root>/scripts/validate_visual_evidence.py \
  --manifest output-tdd/figma-audits/<task>/visual-evidence.json \
  --repo-root <repo>
```

The first command writes task-scoped `validation-receipt.json` bound to the
manifest claim, Git HEAD and tree, the tracked diff, all non-ignored
untracked files, target files, all artifact hashes, and the validator/tool
build hashes. A commit is not required.
The second command fails when any bound content changes, so a previously valid
receipt cannot authorize stale evidence.

Close a row only when the exact asset/state/viewport is aligned, critical
geometry is measured, interactions are observable, and no unexplained
high-salience difference remains. Then move to the next row and finish with the
full `verification-contract.md` regression and reporting contract.
