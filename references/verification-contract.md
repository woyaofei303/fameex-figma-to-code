# Browser Validation and Completion Contract

Load before Playwright. Reuse it for the final response while it remains in context; reload only after context loss. This file is the single browser checklist.

## Artifacts

Create one task-scoped directory:

```text
output-tdd/playwright/<task-timestamp>/
```

Keep only useful review evidence: desktop screenshot at the Figma width, applicable mobile screenshot, failure screenshots named by step, and a trace only when snapshots cannot explain an interaction failure. Keep runtime artifacts under `output-tdd/`; add persistent Playwright tests only for behavior needing regression coverage or when requested.

## Pixel Comparison Protocol

Before comparing geometry, record the capture environment's
`window.innerWidth` and `document.documentElement.clientWidth`. The browser scrollbar
can reduce the layout client width and shift centered content even
when the requested screenshot width matches Figma. Classify that as a render
environment difference. Use device emulation or a documented scrollbar-free
test-only capture for the comparison; never compensate for an automation
artifact in production CSS.

Matching full-page dimensions or section heights does not establish pixel parity.
Compare each long-page section at section-local coordinates after
separating route-shell offsets. Retain the Figma crop, implementation crop,
overlay, and difference image when available. A full-page thumbnail is only an
orientation artifact.

Maintain the frame evidence matrix from intake. Each exact Desktop/H5, state,
and support frame must retain its own structured context, same-node screenshot,
asset inventory, style ledger, actual crop, and overlay/difference evidence. Do
not mark a row verified while an unexplained high-salience difference remains;
if an overlay/difference tool is unavailable, record that environment limitation
and use measured crop/computed-style evidence rather than silently accepting a
visual impression.

Triage visible differences before editing:

Use these labels consistently: environment difference, content/state difference,
asset mismatch, crop/scale mismatch, typography baseline mismatch, and
layout/style mismatch.

1. **Environment difference** — CSS viewport/client width, device scale, font
   availability, scrollbar, browser rendering, or animation frame.
2. **Content/state difference** — Figma sample data, login/eligibility state,
   countdown, active tab, expanded disclosure, loading, or terminal state.
3. **Asset mismatch** — wrong file, hash, intrinsic dimensions, transparency,
   or alpha bounds.
4. **Crop/scale mismatch** — rendered box, aspect ratio, `object-fit`,
   `object-position`, background sizing/position, clipping, or mask.
5. **Typography baseline mismatch** — font family, weight, size, line height,
   letter spacing, text box width, wrapping, and baseline alignment.
6. **Layout/style mismatch** — section-local position, gap, padding, color,
   border, radius, shadow, opacity, and stacking.

Treat a Figma sample balance, sample ranking, or sample countdown as a
content/state difference. Verify its type treatment and layout, but compare the
displayed value against the backend or deterministic acceptance-state value;
do not hardcode design examples or alter business progress merely to improve a
pixel diff.

Change product code only for differences that remain after the exact viewport,
state, asset, and capture environment are aligned. Record the owning code
location and the Figma node/property for every corrected mismatch.

## Browser Checklist

1. Confirm the owning app and exact local route are running.
2. Open the route with the Playwright CLI wrapper and take a fresh snapshot before referencing elements.
   Before accepting interaction evidence, confirm client hydration completed by observing a real component response to a safe action or an attached framework handler. A DOM-only screenshot can look correct while the page remains non-interactive. A successful automation `click` is insufficient unless it produces the expected material state change, such as disabled/loading copy, active-tab content, disclosure state, navigation, or a modal. If hydration is absent, inspect console and HMR health, retry the canonical local host advertised by the dev server, or use a production-style server; record the environment problem instead of reporting the click as passed.
3. At the exact Figma viewport, compare shell, section order, copy, assets, overflow, spacing, alignment, sizing, typography, colors, borders, radii, and clipping with the node screenshot. For a long page, capture comparable section crops at the geometry-ledger coordinates and use overlay/difference inspection when available; a full-page screenshot alone can hide local offsets and styling errors. Inspect computed styles for representative elements in every section; verify actual font family/weight/size/line-height, rendered color, dimensions, border radius, shadow, and breakpoint activation rather than class names alone.
   For every decorative section, inspect the full background stack: images and
   gradients, size/position, mask/clip, glow, box/drop shadow, blur, blend mode,
   opacity, pseudo-elements, and layer order/z-index. Compare the composed
   section crop; checking the foreground card alone is insufficient.
4. Confirm images have non-zero natural dimensions; inspect broken, translucent, cropped, or unexpectedly large assets. Reconcile every visible non-text visual with the asset inventory, including small icons and state variants. A pending placeholder, approximate glyph, missing support-frame asset, or unverified crop blocks an exact-parity claim.
5. Exercise only interactions established by Figma, PRD/backend contract, existing behavior, or explicit user instruction. Check focus, keyboard, disabled, loading, validation, and feedback states when applicable. Confirm disabled appearance and handler behavior agree in terminal/ineligible states; a CTA must not look actionable when its handler intentionally returns without an action.
6. Verify each exercised link in the current branch; otherwise record it as a dependency.
7. Re-snapshot after navigation or material DOM changes. Inspect console/network errors exposed by the workflow.
8. Load `zh-CN`; check raw keys, fallback copy, validation text, metadata, accessibility labels, truncation, overlap, and horizontal overflow. For a source-only namespace, also load at least one supported non-`zh` locale and prove fallback copy renders without raw keys. Otherwise, check another locale only when its translated resource already exists or is explicitly in scope.
9. Capture desktop and applicable mobile evidence. If Figma has one viewport, use it exactly and add repository-derived checks at breakpoint boundaries plus representative intermediate widths. Check cross-breakpoint overflow and prove separate responsive branches retain the same tasks, rewards, status, and action availability.
10. Re-run each affected step after a fix.
11. For each server-backed interaction, capture sanitized evidence for method, path, query, and body field names; the response fields consumed after transport normalization; loading, error, empty, and disabled states; mutation invalidation or refetch; and proof that an inactive tab does not query. Never retain credentials, cookies, tokens, personal data, or file binary.

For timed motion, record observable timestamps or active-index sequences from trigger through completion. Prove immediate input lock/loading copy, exact traversal order and loop count, target stop, result timing, duplicate-click prevention, and cleanup on unmount. Re-run the historical consumer when a shared animation or disclosure primitive changed.

When local authentication or eligibility differs from the Figma state, state the difference. Never treat sample account values or an unlocked design state as backend validation.

## Business Boundary

Do not invent submissions, redirects, API calls, permissions, eligibility, enums, or mock fallbacks. Exercise behavior only when established by selected-node evidence, a PRD/backend contract, existing target behavior, or an explicit instruction. Report unresolved behavior instead of implementing it speculatively.

## Failure Record

For each unresolved failure, report:

```text
Step: <browser action or visual check>
Expected: <evidence-based expectation>
Actual: <observed result>
Artifact: <absolute screenshot or trace path>
Likely code locations:
- <absolute file path>
Reasoning: <short evidence-based mapping>
```

Do not report a vague mismatch without an artifact and likely code location.

## Claim Levels

Use the narrowest claim supported by current evidence:

- **Slice verified**: one manifest slice passed its focused code, route, and applicable API checks.
- **Feature regression verified**: every required slice and affected cross-slice scenario passed; blockers and exclusions are explicit.
- **Release ready**: the fixed candidate also passed [release readiness](release-readiness.md), including review, target build/CI, sign-offs, rollout, rollback, and monitoring.
- **Released and verified**: an explicitly authorized deployment completed and its production-safe smoke plus observation evidence passed.

A focused test, browser pass, verified slice, or Feature Manifest status alone does not prove release readiness. Never collapse these levels into a generic “complete”.

## Final Response Contract

### Targeted response

Return only what the task needs, normally in this order:

1. **Outcome** — implemented scope and whether browser validation completed; no parity claim without evidence.
2. **修改文件** — every changed absolute path in a copyable fenced block.
3. **Validation** — exact commands or browser steps and fresh results. Include focused tests, owning-app checks, touched-locale checks, `git diff --check`, affected viewports, and applicable sanitized network/state evidence. Classify failures as introduced, pre-existing, or environmental.
4. **Failures and Deviations** — omit when none; otherwise use the failure-record shape above.
5. **查看修改** — standalone `git status --short` and touched-path `git diff` commands.

### Strict or feature additions

For `strict-parity`, `feature-delivery`, audits, or release work, add only applicable sections: **Figma Mapping**, **Reuse Decisions**, **Artifacts**, and **Pending Business Questions**. A strict response identifies the manifest and receipt. A feature or release response states its narrowest supported Claim Level.

## Completion Gate

Before claiming completion, apply only gates triggered by the selected mode. A `targeted-change` requires same-node evidence when Figma was supplied, affected-route/viewports, focused checks, and a complete changed-file report; it does not require a strict manifest or receipt. For `strict-parity`, feature, audit, or release work, verify the applicable gates below:

- Structured Figma context and the matching node screenshot preceded implementation.
- The real route and owning app were mapped; the manifest classified controls/assets as `reuse`, `adapt`, `promote`, or `local`.
- The owning component system was preferred; any local control has a recorded behavior/complexity reason.
- Existing icons were checked; a missing icon uses the Figma original or was promoted to `packages/icon` only when semantically reusable.
- No business behavior was guessed; route targets and account assumptions were validated or reported.
- Server-backed work has a completed contract manifest, owning-package test evidence, and sanitized network/state evidence, or a concrete blocker is reported.
- Frontend-owned copy, validation, accessibility labels, and metadata use i18n; Simplified Chinese source keys are complete; no other-language files were generated unless explicitly requested.
- Exact-viewport and responsive evidence exists, or the concrete browser blocker is reported.
- Long-page section crops and the style ledger reconcile Figma values, configured utilities, and rendered computed values; every visible non-text visual has an asset-inventory disposition.
- A one-time standalone activity has a checked removal ledger; route, page code,
  assets, locale keys, shell registrations, tests, and other cross-cutting
  references form an explicit deletion boundary instead of leaking into the
  generic Campaign renderer.
- Every changed file is listed and fresh output supports every pass claim.
- Visual completion has a fresh `validation-receipt.json` generated from a
  frozen candidate snapshot and rechecked against its manifest claim, Git
  HEAD/tree, tracked diff, non-ignored untracked files, explicit target files,
  and artifact hashes.
- The visual validator proves only presentation-slice evidence. Feature
  regression, release-level, and post-release claims also satisfy their
  separate aggregate Claim Level; slice evidence cannot be promoted to a
  broader claim.
