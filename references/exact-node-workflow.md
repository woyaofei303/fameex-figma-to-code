# Exact Node Workflow

Load only for `exact-node-implementation`: a bounded page or component supplied as an exact Figma Design URL with a `node-id`.

## Entry

Use the exact node plus the current repository and worktree. Infer the owning app, route, and code target only from unambiguous repository evidence; when mapping is ambiguous, ask only for the missing target. A PRD is not required, a global Figma inventory is not required, and a Feature Manifest is not required.

Read structured context and a same-node screenshot, map the target and reuse candidates, then follow the parent workflow. Existing repository behavior and confirmed API contracts still own business behavior.

### Large Canvas Protocol

When the supplied node is a large canvas, design board, or long page whose structured response is sparse or truncated, call `get_metadata` first. Locate the route-sized page and relevant state child frames, record their node IDs and dimensions, then fetch structured context and same-node screenshots for those child frames. Treat annotations, explorations, competitor references, dialogs, and alternative states as evidence—not as one deployable page or as page dimensions.

Build a section geometry ledger for a long route. For every route child, record node ID, page-relative `x/y`, local `x/y`, width, height, content-container width, full-bleed versus bounded behavior, clipping, and overlap/z-index relationships. Keep route-shell offsets separate from feature coordinates. Verify each ledger row against a section crop; a plausible full-page height is not proof that internal section geometry matches.

When the global design entry contains support frames for the exact page—desktop/H5 dialogs, loading or terminal states, share sheets, posters, channel selectors, or interaction references—locate them with metadata and fetch each relevant frame directly. Do not implement a dialog or state from the route screenshot alone when a dedicated frame exists elsewhere on the canvas.

Build a frame evidence matrix with one row per exact frame, covering every
supplied Desktop/H5 viewport, state, and support frame. Each row records the
exact node, viewport/state, structured-context read, same-node screenshot,
section geometry ledger, visual-layer inventory, style ledger, actual crop,
overlay/difference artifact, and disposition. Evidence from a desktop frame,
one representative state, or a parent canvas does not stand in for another row.
If metadata does not expose an expected support frame, search the relevant
canvas/page names and record the failed lookup instead of silently deriving it
from a route screenshot.

## Asset and State Intake

Create an asset inventory from every exact node in the slice before editing layout code. Retrieve all Figma-provided icons, images, SVGs, masks, and backgrounds first; download expiring asset URLs immediately into a task-scoped intake directory. Record source node, format, intrinsic and rendered dimensions, hash, and final destination; inspect `packages/icon` and nearby feature assets; compare dimensions and hashes when an apparent repository duplicate exists. Keep combined artwork combined when that is the designer-provided asset. Do not redraw or approximate an asset that Figma or the user supplied.

The inventory is a layout-edit gate: every visible non-text visual must be classified as repository reuse, downloaded Figma asset, authoritative user replacement, or explicitly pending placeholder. Include active/disabled variants, rank badges, arrows, lightning/energy symbols, tab decoration, modal artwork, QR/poster layers, and background masks rather than collecting only the largest banner.

At the start of every new exact route, state, or support-frame intake, perform
the icon/image pass before translating that node into CSS or JSX, even when a
related parent node was already inspected. Use metadata to enumerate child
visuals, retrieve their original exports, and reconcile them with the existing
inventory. A partial structured response is not permission to recreate a
missing icon, glow, mask, or illustration with approximate CSS.

Extend the file inventory into a visual-layer inventory for every exact frame.
Include visible artwork and support/effect layers, including fills, gradients,
masks, glows, adjustment/effect layers, and pseudo-elements even when their
layer name does not look like an exportable asset. For every named slot record:
source node/layer, viewport/state, format/hash, intrinsic/viewBox and alpha
bounds, rendered width/height, `object-fit`/`object-position`, background image,
`background-size`, `background-position`, mask/clip, filter/blur,
`mix-blend-mode`, opacity, z-index, and final repository destination or CSS
owner. The visual-layer inventory is incomplete while a visible background
effect has no source and composition record.

Treat a user-supplied replacement asset as authoritative for its named slot.
Inspect the local file, preserve its intrinsic/viewBox, aspect ratio, alpha
bounds, and requested rendered width/height, and remove the superseded
approximation and duplicate hidden reference from that slot.

### Transparency and Composition Protocol

Before styling around an exported visual, inspect its SVG viewBox or raster
intrinsic size, asset hash, alpha channel and bounds, rendered box, and the
surrounding Figma layers. Preserve transparent cutouts such as ticket notches:
keep the asset wrapper transparent and verify that no parent background, radius,
or pseudo-element fills the negative space. Put any required surface on the
exported asset or on a separately evidenced layer.

Determine whether a fade-shaped export is a visible direct overlay, an alpha
mask source, or only a reference for an equivalent gradient. Do not render a
mask source as an ordinary image merely because Figma returned an image URL.
Record the exact mask size and position, clipping container, `object-fit`, and
`object-position`; compare the composed section crop rather than the isolated
asset preview.

When an asset cannot be retrieved after a recorded attempt, an obvious
temporary placeholder is allowed only when the user permits iterative
placeholder work. Give it a searchable pending marker, retain its source node
and intended dimensions in the inventory, and keep it out of shared icon
packages. Mark its code and report as pending; do not claim exact visual
completion until the original asset is installed and verified.

Build a state matrix when the supplied nodes show variants or states. For each exact node, record viewport, state name, visible/hidden content, copy, CTA style and enabled state, countdown, user data, and artwork. For motion or staged feedback, add an interaction timeline covering trigger, input lock, traversal order, loop count, completion UI, cancellation/unmount, and reduced-motion behavior when established. Fetch structured context and same-node screenshots for each state node. Do not merge state-specific content—for example, a countdown visible only before start must not appear in active or ended states. Create deterministic local acceptance states only in an existing mock/test mechanism, never in production data flow.

## Historical Implementation Reuse

When the user identifies a historical implementation, inspect its route and component tree before creating local UI. Reuse or extract the smallest compatible visual and interaction shell—layout, tabs, ranking presentation, animation engine, modal mechanics, or disclosure control. Keep domain APIs, DTOs, enums, task IDs, reward mappings, copy, and campaign artwork in their owning domain. If a pure capability is promoted, keep the historical page as a consumer and regression-test both routes.

Create a reference route/source map for every user-named reference. Record the
historical route and matching viewport/state, source component, owning hook or
animation/style primitive, source asset, requested visible part, and
`reuse`/`adapt`/`promote`/`reject` decision. Open the real historical route and
inspect its source tree; a Figma screenshot or visual imitation is not evidence
that its implementation was reused.

Treat each user-named reference as a concrete reuse candidate, not merely inspiration: map the visible Figma part to its source component, record whether it is reused, adapted, promoted, or rejected, and explain any rejection. For motion, preserve the requested trigger lock, traversal order, loop count, completion point, result timing, cancellation, and legacy-consumer behavior. Reusing a layout does not authorize copying sample users, dates, rewards, eligibility rules, APIs, or campaign-specific text.

## Boundary

Do not invent API paths, permissions, states, submissions, or navigation from the design. Keep only the dependent behavior blocked when its contract is missing.

Switch to `feature-delivery` when the requested scope expands to multiple routes, product-owned states, cross-app rules, or acceptance that needs requirement-level traceability. In the new Manifest, reuse existing exact-node evidence instead of repeating verified work. Do not retroactively force a scope that stays bounded into a Feature Manifest.

## Evidence

Return the node/route/code mapping, changed files, focused tests, and real-route evidence. State unresolved business or API facts separately. Exact-node verification proves only the bounded scope; broader release claims still use the release modes.
