# FameEX Web Repository Rules

Load during repository mapping and touched-scope validation.

## Workspace Ownership

- Repository: `/Users/julian/fameex-web`.
- Customer Web: `apps/web`; primary components: `@fameex/ui` / `packages/ui`.
- Next.js Admin: `apps/admin`; Futures Admin: `apps/futures-admin`.
- Shared icons: `packages/icon`; utilities and hooks: `packages/utils`.

Resolve the owning app from the existing route and neighboring code. Admin work must follow that app's established Ant Design, Element, or other existing component system; do not import the customer Web system merely for visual similarity.

## Component and Asset Decision Model

Run the candidate audit command from `SKILL.md` against the target and nearby paths. Its line-addressable output is a bounded discovery aid, not a semantic verdict: inspect visible comments, strings, fixtures, and indirect uses manually. If the summary reports omitted candidates, narrow target paths into batches or increase `--limit` while output remains reviewable, rerun until all candidates are visible, and record how coverage was completed.

Search in this order:

1. Owning app's component system.
2. Owning app's shared components and hooks.
3. Adjacent feature components and patterns.
4. Page-local implementation.

Search existing service wrappers, React Query hooks, Zustand stores, tokens, and `packages/icon` alongside the UI search. For each control or asset, answer:

1. Does an existing candidate match the required behavior and semantics?
2. Can supported props, slots, classes, or composition express the visual differences without a fork or fragile override?
3. Is the concept stable across pages or domains, with credible reuse beyond this frame?

Record one manifest classification:

- `reuse`: existing API and styling satisfy the design.
- `adapt`: reuse the existing primitive with supported composition or scoped styling.
- `promote`: add to a shared package because the semantic concept is stable and genuinely cross-page; use it in the same implementation.
- `local`: keep page/feature-local because behavior is incompatible, adaptation cost is disproportionate, or the asset is page-bound.

Give every non-`reuse` item a short reason. Prefer `adapt` over cloning. Do not promote merely to remove duplication from a single page.

### Controls

Use the owning system's Input, Select, Button, Checkbox, form, and feedback primitives when their behavior fits. Preserve accessibility, validation, loading, disabled, focus, and keyboard contracts. A composed control may remain local when shared primitives cannot supply required search, virtualization, formatting, or domain behavior without high complexity; reuse suitable primitives inside it.

Without a confirmed submission or mutation contract, do not leave a form or CTA that can only fail or falsely succeed. Especially for addresses, account identifiers, and proof uploads, disable or hide data-collection controls and the CTA, and keep the unavailable state visible until the contract exists.

### Icons and Artwork

Before choosing an icon, inspect both:

- `packages/icon/output/icon-list.json`
- `packages/icon/svg-files/**`

If no existing icon is suitable, use the original Figma icon asset. Do not draw an approximate SVG, substitute an unrelated glyph, or add a third-party icon package.

Choose `promote` when the icon has stable product semantics, a reusable name, and likely cross-page consumers. Add the Figma SVG to the appropriate `packages/icon/svg-files` category, run the package's established generation workflow, verify `output/icon-list.json`, and use the generated global icon class in the same change. Keep one-off decoration, illustrations, banners, badges, gradients, and strongly page-bound art local even when represented as SVG.

## Implementation Conventions

- Use TypeScript and React function components; match nearby naming, styling, imports, and file layout.
- Use TanStack React Query for server state and Zustand for local UI state when the owning feature does.
- Treat real payloads, PRDs, backend comments, and user corrections as authoritative.
- Trace whether copy is backend-returned, localized, or frontend-composed before editing it.
- Adapt an existing route instead of creating a parallel flow.
- Keep page-specific work local unless reuse evidence justifies promotion.
- Treat Figma React/Tailwind output as design representation, not repository-ready code.
- Use original Figma images/SVGs; verify dimensions, transparency, crop, rendered pixels, and payload size.
- Validate desktop and mobile independently; do not derive mobile only by shrinking desktop.

## Localization

For customer Web, frontend-owned copy and Simplified Chinese source coverage are implementation scope; other languages are a translation-team handoff.

- Reuse the closest namespace; create one only when no existing namespace owns the copy.
- Use `useT('<namespace>')` in client components and `getT(lang, '<namespace>')` for server metadata.
- Localize headings, labels, placeholders, validation, feedback, states, buttons, accessibility labels, and metadata.
- Keep validators and normalizers language-neutral; translate their codes at the rendering boundary.
- Add or update only `zh-CN` / `zh_CN` resources by default. Never generate English, machine translations, placeholders, or copied Chinese in other locales.
- Add another locale only when explicitly requested or supplied; preserve translation-team content and key shape.
- Keep dotted lookups as nested JSON and verify callsite, namespace filename, and JSON path together.
- Do not localize backend-owned content without a confirmed contract.
- When a new namespace has only `zh-CN` / `zh_CN` source resources, validate fallback through at least one supported non-`zh` locale before completion and prove that source copy renders instead of a raw key. If the repository uses an explicit source-only namespace allow-list, add only the new namespace to the existing allow-list, preserve all existing entries, and test that an unregistered namespace retains its previous behavior.
- Never add other-locale files solely to suppress a raw key.
- Check other-locale parity only when those translated resources already exist or are explicitly in scope; never create files solely for parity.

## Route, Shell, Theme, and Account State

Confirm route group, layouts, Header/Footer, navigation, sidebar, breakpoints, and forced-theme behavior. Resolve links against the current branch. Report branch-only destinations as dependencies. Treat Figma profile, eligibility, balance, and status values as samples until existing hooks or contracts establish them; record missing states instead of inventing fallbacks. Use the page's canonical pathname for localized metadata.

## Worktree Safety

Record `git status --short`; preserve unrelated changes. Prefer `git show <branch>:<path>` for read-only inspection. Do not switch branches or create worktrees without need. Keep edits visible and reversible.

## Touched-Scope Validation

Use the owning package and exact touched files:

```bash
pnpm exec biome check --write --no-errors-on-unmatched <touched-files...>
pnpm --filter @fameex/web typecheck
pnpm --filter @fameex/admin typecheck
pnpm vitest --run --cache=false <target-tests...>
git diff --check
git status --short
git diff -- <touched-paths...>
```

Run only the applicable package typecheck. Validate Simplified Chinese JSON and every lookup path deterministically; include other-locale parity only when already in scope. Report repository-wide baseline noise separately. For excluded legacy-admin files, add direct syntax and diff checks appropriate to the language.
