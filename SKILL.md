---
name: fameex-figma-to-code
description: Use when implementing or reproducing an interface in the FameEX web repository from a Figma design URL, exact frame link, or node-id, especially when the result must reuse existing code and finish with browser validation.
---

# FameEX Figma to Code

Turn an exact Figma node into a scoped FameEX implementation with design evidence, repository mapping, real-browser validation, and an evidence-based completion report.

## Input Contract

Require a Figma Design URL containing `node-id`. Accept an optional target route or component path.

When the target is omitted, search the repository and continue only when one existing surface is unambiguous. Ask one blocking question when multiple materially different targets remain. Do not create a parallel route when the selected design belongs to an existing page.

## Dependency Bootstrap

Read [references/dependency-bootstrap.md](references/dependency-bootstrap.md) before loading any required sub-skill.

For each required capability:

1. Resolve it from the current available-skills catalog, personal skills, system skills, or plugin skills.
2. If absent and an exact curated or GitHub source is known, use `skill-installer`.
3. If installation is unavailable or fails, run the bundled dependency bootstrap for that capability.
4. Validate the installed or created `SKILL.md` and its capability prerequisite.
5. Read the new `SKILL.md` directly and resume the original phase in the same turn.

Never overwrite an existing skill directory. Stop and report an invalid existing directory instead of replacing user content. Track dependencies installed or created during the task and include them in the final response.

## Required Sub-Skills

Load each skill only when its phase begins:

- **REQUIRED:** Use `figma` for design context, screenshots, variables, and assets.
- **REQUIRED:** Use `figma-implement-design` before writing UI code.
- **REQUIRED:** Use `playwright` for terminal-driven browser validation.
- **REQUIRED:** Use `superpowers:verification-before-completion` or the local `verification-before-completion` fallback before any completion claim.

Code Connect is optional. Use mappings when the authenticated plan and published Figma components support them. Record and skip entitlement failures without blocking the remaining workflow.

## Workflow

### 1. Preflight and Scope Lock

1. Confirm the current directory is `/Users/julian/fameex-web` or one of its Git worktrees.
2. Inspect the current branch and `git status --short`.
3. Preserve unrelated user changes. If required files overlap existing changes and cannot be edited safely, stop and report the overlap.
4. Parse the Figma `fileKey` and exact `nodeId`.
5. Verify Figma Remote MCP authentication.
6. Resolve or bootstrap all required sub-skills.
7. Verify `npx` and either the Playwright wrapper or direct-CLI fallback before promising browser validation.
8. Resolve the owning app, existing route, route-group shell, and feature surface.
9. For customer Web pages, choose the page namespace and confirm the repository's translation handoff boundary before implementation.

Stop before implementation when the URL lacks a usable node ID, MCP authentication cannot be restored, or the target surface remains ambiguous.

### 2. Collect Design Evidence

Follow the `figma` workflow in this order:

1. Call `get_design_context` for the exact node.
2. If the response is too large or truncated, call `get_metadata`, identify the required section or variant nodes, and call `get_design_context` for those children.
3. Call `get_screenshot` for the same node or exact variant.
4. Fetch variables, Code Connect mappings, and assets when present.

Do not write implementation code until both structured design context and a visual screenshot are available.

Build a working design manifest containing:

- Page hierarchy and section boundaries.
- Layout, constraints, dimensions, overflow, and responsive intent.
- Reusable component candidates.
- Typography, colors, spacing, radii, and design variables.
- Images, SVGs, and icons.
- Visible hover, active, disabled, loading, empty, error, and modal states.
- Copy and annotations.
- Locale namespace, Simplified Chinese source coverage, translation handoff, and copy that must remain backend-provided.
- Authentication assumptions, user-derived values, and navigation targets.
- Business behavior the design does not establish.

### 3. Map the Real Repository

Read [references/fameex-web.md](references/fameex-web.md) before choosing files or components.

Inspect the existing route, route-group layout, adjacent feature code, API hooks, schemas, stores, localization, metadata, forced-theme rules, tests, and responsive patterns. Search shared packages and page-local components before creating anything.

Use this precedence:

```text
Backend contract or PRD -> business behavior
Figma -> layout, copy, visual state, and interaction intent
Repository conventions -> implementation structure
```

Do not infer endpoints, payload fields, enum meanings, permissions, submission effects, navigation, or fallback data from Figma. Implement confirmed visual behavior and report unresolved business behavior as pending; do not hide it in speculative code.

### 4. Plan and Implement Incrementally

Load `figma-implement-design` before editing UI code.

For a large frame, split work into independently verifiable visual slices. Each slice has scope, files, acceptance criteria, dependencies, validation method, and status. Complete one slice and verify it before advancing.

Implementation rules:

- Adapt the existing page when possible.
- Reuse project components, hooks, tokens, icons, API wrappers, and state patterns.
- Treat MCP React/Tailwind as design representation, not repository-ready code.
- Use Figma-provided assets; do not add icon packages or placeholders.
- Keep the patch page-local unless the behavior is genuinely shared.
- For customer-facing `apps/web` pages, route all visible UI copy, validation feedback, empty states, snackbar text, accessibility labels, and metadata through the repository i18n APIs. Keep pure validation logic language-neutral.
- Add or update only the Simplified Chinese locale resource by default. Do not generate other-language translations; FameEX translation staff owns them unless the user explicitly expands the locale scope.
- Verify every navigation target exists in the current branch; report a confirmed dependency instead of silently linking to a branch-only route.
- Do not hardcode authentication, eligibility, account level, or user-derived values as production behavior when only a Figma state establishes them.
- Add focused tests for new pure logic or confirmed interaction behavior.
- Keep unconfirmed business behavior out of the implementation.

### 5. Run the Browser Validation Loop

Read [references/verification-contract.md](references/verification-contract.md), then load `playwright` and follow its CLI-first workflow.

1. Start only the owning app when a server is not already available.
2. Open the target local URL.
3. Take a fresh Playwright snapshot before using element references.
4. Validate the main structure at the Figma frame dimensions.
5. Exercise only interactions established by Figma, the PRD, backend contract, or existing product behavior.
6. Re-snapshot after navigation, modal/menu changes, or substantial DOM updates.
7. For localized customer pages, test `zh-CN`. Test other locales only when their translated resources already exist or the user explicitly includes them in scope.
8. Capture desktop, mobile, and failure screenshots under the required artifact directory.
9. Map each failure to likely files or components before changing code.
10. Repeat implementation and validation until introduced failures are resolved or a real blocker is documented.

Do not finish after code generation. The browser loop is part of the deliverable.

### 6. Validate the Touched Scope

Run the project checks from `references/fameex-web.md`. Classify every failure as introduced, pre-existing, or environmental. Do not broaden the patch solely to clean unrelated baseline failures.

Inspect the final changed-file list and diff. Run `git diff --check` after formatting and tests.

### 7. Report with Evidence

Load `superpowers:verification-before-completion` or the bootstrapped local fallback, then use the exact final-report contract in `references/verification-contract.md`.

Never claim 1:1 parity, passing tests, or completion without fresh command or browser evidence from the current run. If a validation layer could not run, name the unavailable layer and its concrete blocker.

## Stop and Continue Rules

Stop before code changes for:

- Missing or invalid Figma node ID.
- Unrecoverable MCP authentication.
- Ambiguous target page or component.
- Unknown destructive or externally visible behavior required for completion.
- Unsafe overlap with existing user changes.
- An existing dependency directory is invalid and cannot be safely replaced.

Continue with confirmed scope when:

- Code Connect is unavailable.
- A required sub-skill is missing but dependency bootstrap can restore it.
- Repository-wide typecheck has unrelated baseline failures.
- A nonessential interaction is unspecified.
- The selected frame must be decomposed into child nodes.
