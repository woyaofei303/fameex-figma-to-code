# FameEX Web Repository Rules

Load during repository mapping and touched-scope validation.

## Workspace Ownership

- Repository: `<repo-root>` discovered from the active worktree.
- Customer Web: `apps/web`; primary components: `@fameex/ui` / `packages/ui`.
- Next.js Admin: `apps/admin`; Futures Admin: `apps/futures-admin`.
- Shared icons: `packages/icon`; utilities: `packages/utils`; hooks remain in the owning app unless repository evidence shows a shared owner.

Resolve the owning app from the existing route and neighboring code. Admin work must follow that app's established Ant Design, Element, or other existing component system; do not import the customer Web system merely for visual similarity.

## Repository Token Discovery

Resolve the active app's Tailwind config and every inherited preset before translating Figma values into utility classes. For customer Web, read:

- `apps/web/tailwind.config.js`
- `packages/config/tailwind-preset.js`
- `packages/ui/tailwind.config.js` when a shared UI component owns the element
- `packages/utils/classNames.ts` when merged or conditional utilities can affect the result

### Style Uncertainty Protocol

When a class name, token, breakpoint, plugin utility, or component default is uncertain, pause styling and resolve it from the repository instead of guessing. Start with:

```bash
sed -n '1,220p' apps/web/tailwind.config.js
sed -n '1,380p' packages/config/tailwind-preset.js
sed -n '1,180p' packages/ui/tailwind.config.js
rg -n "borderRadius|fontSize|spacing|screens|colors|boxShadow|heroui|classNames|tailwind-variants" \
  apps/web packages/config packages/ui packages/utils
```

Follow imports recursively until the final value or plugin default is known. If the owning primitive is built with HeroUI, `tailwind-variants`, `cn`, or `classNames`, inspect that component's variant/style file and merge behavior too. Do not infer output from a utility name alone.

Resolve uncertain styles through the complete cascade:

```text
active app config -> inherited preset -> plugin/component defaults ->
component variants -> call-site conditions -> merged class string ->
rendered computed style
```

Record which source wins when values conflict. Reading only
`apps/web/tailwind.config.js` is insufficient when it spreads an inherited
preset, and reading only the preset is insufficient when a component variant or
merge helper changes the final class. Do not bulk-replace utilities by their
names; resolve each affected element's Figma value, owning primitive, final
class, and computed value.

Create a compact style ledger for each implemented section:

```text
Figma node/property/value -> repository token or explicit value -> rendered computed value
```

Cover container width, position/spacing, typography, color under the active theme, border, radius, shadow, asset dimensions/crop, and responsive activation. A token-name match without a computed-value match is a failure. Prefer an exact repository token; use an arbitrary value only when the final config has no exact token.

For a section with decorative composition, expand the ledger into the complete
background stack: solid fills, background images/gradients, size/position,
masks, glows, box/drop shadows, `filter`/`backdrop-filter` blur, blend mode,
opacity, pseudo-elements, clipping, and layer order/z-index. Resolve each layer
from the exact Figma hierarchy or an authoritative supplied asset, then confirm
the rendered stack in a section-local crop. Matching the main foreground box
while omitting a faint glow or filling a transparent cutout is still a style
failure.

Do not assume Tailwind default utility values from memory or from another repository. The FameEX preset currently defines:

- `rounded` = `4px`
- `rounded-sm` = `6px`
- `rounded-m` = `8px`
- `rounded-lg` = `16px`
- `rounded-xl` = `32px`
- `xl` = `1440px`
- maximum-width aliases are declared as `<sm`, `<md`, `<lg`, `<xl`, and `<2xl`

Use the configured maximum-width alias in responsive classes, for example
`<md:text-[12px]`. Do not assume an undeclared-looking `max-sm:` or `max-md:`
variant produces CSS merely because it appears in the rendered class string.
At the exact boundary viewport, inspect the computed style and overflow after a
fresh compilation; a DOM class with no matching rule is a responsive failure.

For standard Figma typography, prefer the preset's semantic size/line-height pair:

- `text-h2` = `28px / 33.6px`
- `text-h3` = `24px / 36px`
- `text-h4` = `20px / 30px`
- `text-subtitle` = `16px / 24px`
- `text-body-regular` = `14px / 21px`
- `text-body-s` = `12px / 18px`

Do not substitute Tailwind defaults such as `text-xl` / `text-sm` / `text-xs` merely because the font size matches: their default line heights can differ from the FameEX Figma styles and shift centered content, stacked task rows, and progress baselines. Use an explicit arbitrary size/line-height only for a Figma style that has no matching preset token.

Use the project token whose configured value exactly matches the Figma value. Use an arbitrary value only when no owning-app token matches and the design requires that exact value. Inspect the same preset for custom spacing, font size/line height, colors, shadows, and breakpoints instead of assuming stock Tailwind semantics.

After implementation, inspect the rendered element's computed style at the exact Figma viewport. A familiar-looking class name is not evidence: verify actual `border-radius`, font size/line height, font weight/family, color, dimensions, and responsive activation. For example, a Figma `8px` radius is `rounded-m`, not `rounded-lg`, in customer Web. Theme-backed colors must be checked as rendered RGB/RGBA values under the required light/dark mode; the CSS-variable token name alone does not prove the visual color.

In the current customer Web preset, map a Figma `8px` radius to
`rounded-m` and a Figma `16px` radius to `rounded-lg`. This mapping remains
conditional on the active config and the rendered result: a HeroUI radius,
component variant, inline style, or later merged utility can override the token.
Keep an intentional 16px card on `rounded-lg`; do not globally replace every
occurrence while fixing an 8px control.

Derive each responsive activation breakpoint from both the configured screen value and the layout's real minimum width. A fixed-width desktop branch must not replace the mobile/tablet branch before it fits; make it fluid or activate it at a fitting breakpoint. Test the exact breakpoint boundaries and intermediate widths, and never use `overflow-x-hidden` to conceal a clipped layout.

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

Across sibling tabs, reuse the owning Admin page's field/control width pattern. Do not copy a one-frame magic width or create a feature-global width without reuse evidence.

Without a confirmed submission or mutation contract, do not leave a form or CTA that can only fail or falsely succeed. Especially for addresses, account identifiers, and proof uploads, disable or hide data-collection controls and the CTA, and keep the unavailable state visible until the contract exists.

### Icons and Artwork

Before choosing an icon, inspect both:

- `packages/icon/output/icon-list.json`
- `packages/icon/svg-files/**`

If no existing icon is suitable, use the original Figma icon asset. Do not draw an approximate SVG, substitute an unrelated glyph, or add a third-party icon package.

Choose `promote` when the icon has stable product semantics, a reusable name, and likely cross-page consumers. Add the Figma SVG to the appropriate `packages/icon/svg-files` category, run the package's established generation workflow, verify `output/icon-list.json`, and use the generated global icon class in the same change. Keep one-off decoration, illustrations, banners, badges, gradients, and strongly page-bound art local even when represented as SVG.

## Implementation Conventions

- Use TypeScript and React function components in typed apps; in Legacy Admin, preserve its existing JavaScript unless migration is explicitly in scope. Match nearby naming, styling, imports, and file layout.
- Use TanStack React Query for server state and Zustand for local UI state when the owning feature does.
- Treat real payloads, PRDs, backend comments, and user corrections as authoritative.
- Resolve conflicts explicitly: confirmed PRD/backend/user corrections own business rules and data; exact Figma nodes own visual structure and styling. Figma sample dates, users, rewards, balances, and rankings are evidence for appearance, not production constants.
- Trace whether copy is backend-returned, localized, or frontend-composed before editing it.
- Choose route ownership from confirmed lifecycle and repository evidence. Adapt an
  existing generic route only when it owns the feature contract; use the
  one-time activity isolation rules below when the user or product scope requires
  a standalone, removable campaign.
- Keep page-specific work local unless reuse evidence justifies promotion.
- Treat Figma React/Tailwind output as design representation, not repository-ready code.
- Use original Figma images/SVGs; verify dimensions, transparency, crop, rendered pixels, and payload size.
- Keep presentation decisions such as progress visibility, card width variant, and disclosure state in explicit display configuration when they are not derivable from business state. Do not infer a progress bar from a numeric target: a task can have a target while the approved design intentionally hides progress.
- Preserve requested visual reuse at the smallest stable layer. A historical ranking, lottery, tab, FAQ disclosure, or share implementation may supply layout and interaction mechanics while the new campaign keeps its own theme, copy, assets, domain state, and API contract.
- Validate desktop and mobile independently; do not derive mobile only by shrinking desktop.
- Keep responsive branches on the same business state, DTO values, reward/task visibility, and action semantics. Presentation may differ; business content must not disappear or conflict when desktop and H5 use separate component trees. Trace every changed shared fixture/model field through all responsive consumers, even when the requested visual change names only one viewport.

## One-Time Activity Isolation

When the user or product owner identifies a one-time standalone activity whose
route, code, and artwork should be removable after the campaign, preserve that
lifecycle boundary instead of forcing the page into a generic Campaign renderer.
For customer Web, default to these owners unless repository evidence establishes
another existing convention:

- canonical route: `apps/web/src/app/[lang]/.../<slug>/page.tsx`
- page domain: `apps/web/src/apps/Marketing/<Feature>/`
- page-bound artwork: `apps/web/public/static/marketing/<slug>/`
- page-owned Simplified Chinese copy: a removable feature namespace or an
  explicitly enumerated key subtree

Reuse shared primitives, hooks, API clients, interaction engines, and historical
layout mechanics at their smallest stable layer. Keep the one-time activity's
orchestration, fixtures, assets, reward mapping, theme, and copy inside its
feature boundary. Do not make the generic Campaign renderer import the
standalone activity, and do not copy domain-specific World Cup or historical
campaign APIs merely to reuse their visual shell.

Create a removal ledger before implementation. List the canonical route, feature
directory, asset directory, locale keys, tests, pathname constants, shell/theme
registrations, sitemap/navigation entries, analytics registrations, and every
shared primitive intentionally changed. After implementation, search for the
route slug and feature name outside the feature directories; every hit must be
either in the removal ledger or removed. A standalone route may still use the
repository's Header/Footer route group, but cross-cutting shell hooks must remain
small and explicitly removable.

Use deterministic mock states only through an established local/test mechanism.
Do not make a production query parameter, hard-coded activity ID, or sample
fixture the real data source merely to make the isolated route render.

## Localization

For customer Web, frontend-owned copy and Simplified Chinese source coverage are implementation scope; other languages are a translation-team handoff.

- Body copy remains in the owning feature namespace; use `useT('<namespace>')` in client components and create a namespace only when no existing one owns the copy.
- Customer Web page-level metadata belongs to the dedicated `tdk` namespace. For frontend-owned static metadata, use `const { t } = await getT(lang, 'tdk')` with `tdk:<route-key>.title`, `tdk:<route-key>.description`, and `tdk:<route-key>.keyWords`; follow the established route-key shape, while the Next.js `Metadata` field remains `keywords`.
- Do not add a `meta` subtree to a feature namespace. When migrating one, trace all consumers before removing it and validate the `tdk` lookup plus non-`zh` fallback.
- Backend-owned dynamic SEO remains backend-owned; do not duplicate article or CMS metadata in `tdk`.
- Localize headings, labels, placeholders, validation, feedback, states, buttons, and accessibility labels.
- Keep validators and normalizers language-neutral; translate their codes at the rendering boundary.
- Add or update only `zh-CN` / `zh_CN` resources by default. Never generate English, machine translations, placeholders, or copied Chinese in other locales.
- Add another locale only when explicitly requested or supplied; preserve translation-team content and key shape.
- Keep dotted lookups as nested JSON and verify callsite, namespace filename, and JSON path together.
- Do not localize other backend-owned content without a confirmed contract.
- When a new namespace has only `zh-CN` / `zh_CN` source resources, validate fallback through at least one supported non-`zh` locale before completion and prove that source copy renders instead of a raw key. If the repository uses an explicit source-only namespace allow-list, add only the new namespace to the existing allow-list, preserve all existing entries, and test that an unregistered namespace retains its previous behavior.
- A shared `tdk` namespace needs key-level fallback, not namespace-level fallback. When a route key exists only in Simplified Chinese, add that exact key to the repository's `ZH_CN_SOURCE_ONLY_TDK_KEYS`, preserve translated keys, add a focused loader test, and verify one supported non-`zh` route without a raw key.
- Never add other-locale files solely to suppress a raw key.
- Check other-locale parity only when those translated resources already exist or are explicitly in scope; never create files solely for parity.

For touched-scope lookup coverage, compare callsites with the Simplified Chinese
namespace leaves before completion:

```bash
/usr/bin/python3 <skill-root>/scripts/audit_i18n_lookups.py \
  --namespace-json /absolute/path/to/zh-CN/namespace.json \
  --source /absolute/path/to/page.tsx \
  --source /absolute/path/to/feature-directory \
  --key explicit.dynamic.expansion \
  --json
```

Repeat `--source` for each bounded file or directory. Template and computed
lookups are not inferred; provide every exact expansion with repeatable `--key`.
For a shared namespace such as `tdk`, add `--allow-unused` so unrelated page keys
remain reported but do not fail the touched-page audit. Missing keys still fail.
For recognized literal `useT` or `getT` bindings, the scanner ignores unprefixed
`t()` calls owned by another namespace, so nearby feature sources can be included.
This audit does not change the source-only namespace or fallback rules above.

## Route, Shell, Theme, and Account State

Confirm route group, layouts, Header/Footer, navigation, sidebar, breakpoints, and forced-theme behavior. Check whether an existing shell slot is feature-flag or experiment gated before treating a locally absent shell element as missing. Do not add a duplicate Header or Footer inside a feature page when the route group already owns it; validate the production/default flag behavior separately from a local flag-loading failure. Resolve links against the current branch. Report branch-only destinations as dependencies. Treat Figma profile, eligibility, balance, and status values as samples until existing hooks or contracts establish them; record missing states instead of inventing fallbacks. Use the page's canonical pathname for localized metadata.

## Worktree Safety

Record `git status --short`; preserve unrelated changes. Prefer `git show <branch>:<path>` for read-only inspection. Do not switch branches or create worktrees without need. Keep edits visible and reversible.

## Touched-Scope Validation

Use the owning package and exact touched files. Choose only the applicable app block; do not combine all typechecks.

Customer Web tests use the root Vitest configuration because its aliases resolve Web paths:

```bash
pnpm exec biome check --write --no-errors-on-unmatched <touched-files...>
pnpm --filter @fameex/web typecheck
pnpm vitest --run --cache=false <web-target-tests...>
git diff --check
```

Next.js Admin tests must run in the Admin package context so `@` resolves to `apps/admin/src` instead of `apps/web/src`:

```bash
pnpm exec biome check --write --no-errors-on-unmatched <touched-files...>
pnpm --filter @fameex/admin typecheck
pnpm --filter @fameex/admin exec vitest --run --cache=false <admin-target-tests...>
git diff --check
```

Use the equivalent package-scoped command for `@fameex/futures-admin`. For excluded legacy Admin JavaScript, do not claim Biome coverage; add direct syntax and diff checks:

```bash
node --check <legacy-admin-files...>
git diff --check
```

Finish every block with `git status --short` and `git diff -- <touched-paths...>`. Validate Simplified Chinese JSON and in-scope static lookups with the scanner; enumerate dynamic or template paths with `--key`. Include other-locale parity only when already in scope. Report repository-wide baseline noise separately.
