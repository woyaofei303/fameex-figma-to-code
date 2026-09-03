---
name: fameex-figma-to-code
description: Use when implementing or auditing FameEX frontend work from a Figma Design URL, exact node, visual correction, or product requirement, including strict pixel-parity and multi-route feature delivery.
---

# FameEX Figma to Code

Turn confirmed design and product evidence into the smallest correct change in the owning FameEX app. Preserve existing behavior and unrelated work.

## Preflight

Record repository, worktree, branch, dirty state, app, route, locale namespace, and loaded skill root. Read [references/capability-index.md](references/capability-index.md) and resolve only capabilities triggered by the selected mode.

Select the smallest mode that fits:

- `targeted-change` (default): an existing UI/style/copy/asset/component/dialog change. Load [references/exact-node-workflow.md](references/exact-node-workflow.md); validate only affected states and viewports. No full visual manifest, receipt, or viewport matrix.
- `strict-parity`: explicit 逐帧、逐像素、每个距离要求; a new page; multiple linked states; complex motion; or coupled Desktop/H5 work. Load the same reference and [references/visual-fidelity-loop.md](references/visual-fidelity-loop.md); converge one section, one state, and one viewport at a time with the existing `exact-node-implementation` evidence schema, RGBA checks, viewport matrix, and receipt.
- `feature-delivery`: a PRD, multi-route work, or cross-app behavior. Load [references/product-delivery-workflow.md](references/product-delivery-workflow.md) and build the Feature Manifest before implementation.
- `slice-implementation`: implement one fully mapped Feature Manifest slice.
- `audit-existing`: load [references/existing-implementation-audit.md](references/existing-implementation-audit.md) against a fixed merge-base.
- `release-readiness` / `post-release-validation`: use [references/release-readiness.md](references/release-readiness.md) only when explicitly requested. Deployment still requires explicit authorization.

## Workflow

1. **Collect evidence.** When Figma is supplied, load `figma` and require structured context plus a same-node screenshot from an authenticated exact-node read in the current task. A `figma` skill, MCP registration, or OAuth alone is insufficient. Do not infer product behavior from visuals.
2. **Map code.** Read [references/fameex-web.md](references/fameex-web.md); inspect the real route, adjacent implementation, responsive rules, tests, and i18n. Run `scripts/audit_reuse.py` only when choosing or adding a component, asset, hook, API wrapper, or when historical reuse is requested. Classify relevant candidates as `reuse`, `adapt`, `promote`, or `local`.
3. **Lock contracts.** PRD/backend owns behavior, Figma owns presentation, repository evidence owns structure. For server-backed work only, read [references/api-integration.md](references/api-integration.md) and complete the contract manifest for each interaction or independently releasable slice. Keep unknown behavior unavailable.
4. **Implement.** Load `figma-implement-design` for visual implementation. Reuse repository components/assets. Put changed frontend copy in Simplified Chinese i18n; inspect other locales only when touched or required.
5. **Verify.** For visible UI or an explicit browser audit, read [references/verification-contract.md](references/verification-contract.md), load `playwright`, and exercise the real route at affected viewports. Run focused tests, owning-app checks, locale checks when touched, and `git diff --check`. Store useful artifacts under `output-tdd/`.
6. **Report.** Load `superpowers:verification-before-completion`; make only claims supported by fresh evidence. Do not commit, push, publish, install, authenticate, or modify Codex configuration without the required user request or approval.

If a triggered capability is absent, ask before any installation or configuration change, then use [references/dependency-bootstrap.md](references/dependency-bootstrap.md) and resume the original task. Code Connect remains optional.
