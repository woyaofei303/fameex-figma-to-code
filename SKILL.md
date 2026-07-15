---
name: fameex-figma-to-code
description: Use when implementing or reproducing a FameEX frontend interface from a Figma Design URL, exact frame link, or node-id, especially when the work must fit an existing route, component system, localization model, and browser-verified workflow.
---

# FameEX Figma to Code

Implement the exact Figma node in its owning FameEX app. Preserve repository behavior, reuse the correct design system, and support completion claims with fresh evidence.

## Input and Preflight Gates

Require a Figma Design URL with `node-id`; accept an optional route or component path. When no target is supplied, continue only if repository evidence identifies one surface unambiguously. Never create a parallel route for an existing page.

Before editing, record:

- Repository absolute path, Git worktree path, current branch, and dirty state.
- Owning app, target route, and feature surface.
- Loaded skill root, used to resolve bundled scripts and references. When skill maintenance is in scope, distinguish the source Git repo (`/Users/julian/fameex-figma-to-code`) from the installed runtime skill (`/Users/julian/.codex/skills/fameex-figma-to-code`).

Preserve unrelated changes. Stop on an invalid node ID, unrecoverable Figma authentication, ambiguous target, unsafe overlap, or required destructive/external behavior whose contract is unknown.

Read [references/dependency-bootstrap.md](references/dependency-bootstrap.md) before resolving missing skills. Never overwrite an existing skill directory.

After preflight, an existing branch selects `audit-existing`: fix a merge-base, create a route/node/code manifest, and load [references/existing-implementation-audit.md](references/existing-implementation-audit.md) before repository mapping.

## Required Sub-Skills

Load only when its phase begins:

- **REQUIRED:** `figma` for structured context, screenshot, variables, and assets.
- **REQUIRED:** `figma-implement-design` before UI edits.
- **REQUIRED:** `playwright` for browser validation.
- **REQUIRED:** `superpowers:verification-before-completion`, or the bundled fallback, before completion claims.

Code Connect is optional. Record entitlement failures and continue.

## Seven Phases

### 1. Lock Scope

Parse the exact `fileKey` and `nodeId`; verify Figma access, required skills, browser tooling, owning app, existing route, shell, and locale namespace. Record the preflight environment above.

### 2. Collect Design Evidence

Load `figma`. Fetch `get_design_context` and `get_screenshot` for the same node before coding. If context is truncated, use metadata to fetch only required children. Fetch variables, mappings, and original assets when relevant.

Create a design manifest for hierarchy, responsive constraints, tokens, copy, assets, states, navigation, account assumptions, and unknown business behavior. Classify every control and asset as `reuse`, `adapt`, `promote`, or `local`; add a short reason for every non-`reuse` decision.

### 3. Map the Repository

Read [references/fameex-web.md](references/fameex-web.md). Inspect the route, shell, adjacent feature, services, stores, i18n, tests, and responsive conventions. Run one initial bounded candidate audit from the loaded skill root:

```bash
/usr/bin/python3 <skill-root>/scripts/audit_reuse.py --repo-root <repo> <absolute-target-paths...>
```

If the summary reports `omitted > 0`, split target paths into narrower batches or raise `--limit` while output remains reviewable; rerun until every candidate is visible. Record the commands and coverage, then judge visible results in context.

Use this authority order: backend contract or PRD for business behavior; Figma for visual and interaction intent; repository conventions for implementation structure. Do not infer APIs, permissions, enums, submission effects, or fallback data from Figma.

When the selected node or existing branch includes server-backed queries, mutations, uploads, or status fields, read [references/api-integration.md](references/api-integration.md) and complete its contract manifest before UI edits. Skip that reference for purely presentational work.

### 4. Implement in Slices

Load `figma-implement-design`. For large frames, implement independently verifiable slices. Follow the component and asset decision model in `references/fameex-web.md`; prefer the owning app's component system and use original Figma assets when no suitable shared icon exists.

Route frontend-owned visible copy, validation, accessibility labels, and metadata through i18n. Add or modify only Simplified Chinese (`zh-CN`/`zh_CN`) resources by default. Never create translations or Chinese placeholders in other locales; translation staff owns them unless the user explicitly expands scope.

Keep unconfirmed business behavior out of production code. For server-backed work, implement from the completed contract manifest and preserve query/mutation lifecycle evidence. Add focused tests for confirmed logic or interactions.

### 5. Validate in a Browser

Read [references/verification-contract.md](references/verification-contract.md), load `playwright`, and follow its single browser checklist. Validate `zh-CN`, the exact Figma viewport, applicable responsive behavior, confirmed interactions, assets, navigation, console output, and account-state differences. Store review artifacts under `output-tdd/`.

### 6. Validate the Touched Scope

Run owning-app formatting, focused tests, typecheck, locale-path checks, and `git diff --check` as specified in `references/fameex-web.md`. Classify failures as introduced, pre-existing, or environmental; do not expand scope to fix unrelated baselines.

### 7. Report Evidence

Load the verification skill and use the exact final-response contract in `references/verification-contract.md`. Include changed files, commands/results, browser artifacts, reused/adapted/promoted/local decisions, dependencies, and unresolved business questions. Never claim parity, passing checks, or completion without fresh current-run evidence.

## Continue Conditions

Continue within confirmed scope when Code Connect is unavailable, a dependency can be bootstrapped, global checks have unrelated baseline failures, a nonessential interaction is unspecified, or a large node must be decomposed. Report the constraint instead of inventing behavior.
