# FameEX Web Repository Rules

Load this reference during repository mapping and touched-scope validation.

## Workspace and Ownership

- Repository: `/Users/julian/fameex-web`.
- Customer web: `apps/web`.
- Next.js admin: `apps/admin`.
- Futures admin: `apps/futures-admin`.
- Shared UI: `packages/ui`.
- Shared icons: `packages/icon`.
- Shared utilities and hooks: `packages/utils`.

Resolve the owning app from the existing route and neighboring code. Do not assume every Figma frame belongs to `apps/web`.

## Reuse Order

Search in this order before creating code:

1. Existing target page and page-local components.
2. Adjacent feature components, hooks, schemas, and utilities.
3. `@fameex/ui` and `packages/ui`.
4. `packages/icon`.
5. Existing service/API wrappers and React Query hooks.
6. Existing Zustand stores for local UI state.

Extend a matching component when its API supports the design. Do not move a page-local pattern into a shared package unless multiple real consumers require it.

## Implementation Conventions

- Use TypeScript and React function components.
- Follow nearby naming, styling, import, and file-organization patterns.
- Use TanStack React Query for server state and request lifecycle concerns.
- Use Zustand for local client/UI state when the feature already follows that pattern.
- Treat real payloads, PRDs, backend field comments, and user corrections as authoritative.
- Trace whether UI copy is backend-returned, localized, or frontend-composed before changing it.
- Prefer adapting an existing page over creating a new route or parallel flow.
- Keep page-specific work local unless the user explicitly expands the scope.

## Design and Assets

- Treat Figma React/Tailwind output as an intermediate representation.
- Reuse project tokens and components while preserving the selected node's visual intent.
- Do not add icon packages.
- Use Figma-provided image and SVG sources when available; do not create placeholders.
- Inspect exported asset dimensions, transparency, rendered pixels, and byte size. If an MCP asset is blank, cropped, or unexpectedly translucent, re-fetch the exact child node or screenshot and verify the rendered result before coding around it.
- Prefer the repository-supported web format and avoid committing oversized raw design exports when a visually equivalent optimized asset can be produced without changing the design.
- Validate desktop and mobile independently. Do not derive mobile solely by shrinking desktop dimensions.

## Localization

For a complete customer-facing `apps/web` page, wiring the interface to i18n and providing the Simplified Chinese source copy are part of implementation. Other-language translation is a separate handoff owned by FameEX translation staff.

- Reuse the closest existing namespace. Create a page namespace only when no existing namespace owns the copy.
- Use `useT('<namespace>')` in client components and `getT(lang, '<namespace>')` for server metadata.
- Localize every visible string owned by the frontend: headings, labels, placeholders, validation feedback, snackbar text, empty/loading/error states, button copy, accessibility labels, and SEO metadata.
- Keep pure schemas, validators, and normalizers language-neutral. Return error codes or field identities and translate at the rendering boundary.
- Add or update only `zh-CN` or `zh_CN` locale resources by default. Do not add English copies, machine translations, placeholder translations, or duplicate Simplified Chinese into other locale files.
- Add other locales only when the user explicitly requests them or supplies translation content. Treat translation-team output as authoritative and preserve its key tree.
- Keep dotted lookup paths as nested JSON objects. Verify the callsite, namespace filename, and JSON shape together.
- Trace whether copy is backend-returned, localized, or frontend-composed before changing it. Do not move backend-owned content into locale files without a confirmed contract.
- Validate the Simplified Chinese JSON paths with a deterministic check. If translated resources for the namespace already exist or are explicitly in scope, also check their key parity and long-copy layout; do not create translations merely to satisfy parity.
- Browser-check `zh-CN` at desktop and mobile widths when responsive behavior applies. Check additional locales only when their resources already exist or the user explicitly includes them.
- Keep page-local locale work page-local. Do not change the global Header language selector unless the user explicitly requests it.

## Route, Shell, Theme, and Account State

- Confirm the target route, route group, layouts, Header/Footer inclusion, mobile navigation, and any page-local sidebar before implementation.
- Check forced-theme hooks and shell styling so a dark Figma page does not accidentally alter other routes.
- Resolve every link and redirect against the current branch. When a destination exists only in a PRD or another branch, report it as a dependency and avoid presenting the navigation as fully validated.
- Distinguish Figma sample values from real account state. Trace login state, VIP eligibility, profile data, and server-derived status through existing hooks or contracts before wiring them.
- Validate the available logged-in, logged-out, eligible, ineligible, loading, and error states that are confirmed by Figma, PRD, backend contract, or existing code. Record missing contracts instead of inventing fallbacks.
- Localize metadata and use the same canonical pathname constant as the page route.

## Worktree Safety

- Run `git status --short` before editing.
- Preserve all unrelated user changes.
- Prefer `git show <branch>:<path>` for read-only inspection of another branch.
- Do not switch branches or create a worktree unless required by the user or by overlapping changes.
- Keep every edit visible and reversible.

## Validation Commands

Format or check touched JS, TS, TSX, and JSON files:

```bash
pnpm exec biome check --write --no-errors-on-unmatched <touched-files...>
```

Use the owning package typecheck:

```bash
pnpm --filter @fameex/web typecheck
pnpm --filter @fameex/admin typecheck
```

Run focused Vitest without the Vite cache when relevant:

```bash
pnpm vitest --run --cache=false <target-tests...>
```

Always finish touched-scope inspection with:

```bash
git diff --check
git status --short
git diff -- <touched-paths...>
```

For a new or expanded locale namespace, assert Simplified Chinese JSON validity and verify every code lookup path exists. When other translated locale files already exist or are in scope, assert parity across those files too. A direct JSON traversal is preferred over depending on runtime i18next resolution for this structural check.

Repository-wide typecheck has known baseline noise. Report whether failures are introduced, pre-existing, or environmental; do not modify unrelated files to make the global command green.

Legacy admin paths may be excluded from normal Biome coverage. For those files, add direct syntax checks and diff inspection appropriate to the language.
