---
name: fameex-figma-to-code
description: Use when implementing or auditing a FameEX frontend feature from a product requirement, Figma Design URL, exact frame, or node-id, especially across routes, states, APIs, localization, and browser verification.
---

# FameEX Figma to Code

Turn confirmed product and design evidence into code in the owning FameEX app. Preserve behavior, reuse the design system, and prove results.

## Preflight

Record repository, worktree, branch, dirty state, app, route, locale namespace, and loaded skill root. Preserve unrelated changes. Stop only the unsafe or unverified dependent part.

Read [references/capability-index.md](references/capability-index.md); resolve only required or triggered capabilities. If the skill is missing or required Figma tools fail, follow [references/dependency-bootstrap.md](references/dependency-bootstrap.md), validate, and resume the original task. Never overwrite a skill directory. A `figma` skill, MCP registration, or OAuth alone is insufficient: require an authenticated exact-node read in the current task.

Select one mode:

- `feature-delivery`: complete a PRD or multi-page feature intake with its global design entry. Load [references/product-delivery-workflow.md](references/product-delivery-workflow.md), build the Feature Manifest, and do not code until slices and conflicts are mapped.
- `slice-implementation`: load that manifest; require the slice's exact nodes, route, behavior, and API status.
- `audit-existing`: fix a merge-base, create a route/node/code manifest, and load [references/existing-implementation-audit.md](references/existing-implementation-audit.md).
- `release-readiness`: freeze the candidate commit, aggregate verified slices, and load [references/release-readiness.md](references/release-readiness.md).
- `post-release-validation`: after an authorized deployment, use the same reference for production-safe smoke, monitoring, and rollback evidence.

## Workflow

1. **Collect evidence.** Load `figma`; fetch structured context and same-node screenshot. Capture hierarchy, constraints, tokens, copy, assets, states, navigation, account assumptions, and unknowns.
2. **Map code.** Read [references/fameex-web.md](references/fameex-web.md); inspect route, shell, adjacent code, services, state, i18n, tests, and responsive patterns. Run:

   ```bash
   /usr/bin/python3 <skill-root>/scripts/audit_reuse.py --repo-root <repo> <absolute-target-paths...>
   ```

   Classify controls/assets as `reuse`, `adapt`, `promote`, or `local`; explain non-reuse.
3. **Lock contracts.** PRD/backend owns behavior, Figma visuals, repository structure. Never infer APIs, permissions, enums, submissions, or production fallback data. For server-backed work, load [references/api-integration.md](references/api-integration.md) and complete a contract manifest for each interaction or independently releasable slice.
4. **Implement.** Load `figma-implement-design`; use owning components and original assets. Put frontend copy, validation, accessibility labels, and metadata in i18n. Modify only Simplified Chinese by default. Keep unconfirmed behavior unavailable; test confirmed behavior.
5. **Verify route.** Read [references/verification-contract.md](references/verification-contract.md), load `playwright`, and check `zh-CN`, exact viewport, responsive layout, interactions, assets, navigation, console/network, and account states. Store useful artifacts under `output-tdd/`.
6. **Verify scope.** Run owning-app formatting, focused tests, typecheck, locale checks, and `git diff --check`; classify failures as introduced, pre-existing, or environmental.
7. **Close the feature.** Slice verification is not release readiness. Use `release-readiness` for cross-slice regression, review, build/CI, sign-offs, rollout, rollback, and monitoring; use `post-release-validation` after deployment.
8. **Report evidence.** Load `superpowers:verification-before-completion` or fallback. Claim only freshly verified results.

Code Connect remains optional. Missing optional capability or unrelated baseline failure does not block confirmed slices.
