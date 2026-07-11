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
- Validate desktop and mobile independently. Do not derive mobile solely by shrinking desktop dimensions.

## Localization

Modify only Simplified Chinese (`zh-CN` or `zh_CN`) locale files unless the user explicitly requests other languages. Do not fill other locales speculatively.

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

Repository-wide typecheck has known baseline noise. Report whether failures are introduced, pre-existing, or environmental; do not modify unrelated files to make the global command green.

Legacy admin paths may be excluded from normal Biome coverage. For those files, add direct syntax checks and diff inspection appropriate to the language.
