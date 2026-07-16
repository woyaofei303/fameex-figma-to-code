---
name: fameex-figma-to-code
description: Use when implementing or reproducing a FameEX frontend interface from a Figma Design URL, exact frame link, or node-id, especially when the work must fit an existing route, component system, localization model, and browser-verified workflow.
---

# FameEX Figma to Code

Implement the exact Figma node in its owning FameEX app. Preserve behavior, reuse its design system, and support claims with fresh evidence.

## Preflight

Require a Figma Design URL with `node-id`; accept an optional route or component path. Without a target, continue only when the repository identifies one surface unambiguously. Never create a parallel route.

Record the repository, worktree, branch, dirty state, owning app, route, locale namespace, and loaded skill root. Preserve unrelated changes. Stop for an invalid node, unrecoverable authentication, ambiguous target, unsafe overlap, or unknown destructive/external behavior.

Read [references/capability-registry.md](references/capability-registry.md) before work and resolve only required or triggered capabilities. If the skill is missing or required Figma tools fail, follow [references/dependency-bootstrap.md](references/dependency-bootstrap.md), validate the result, and resume the original task. Never overwrite a skill directory. A `figma` skill, MCP registration, or OAuth alone is insufficient: require an authenticated exact-node read in the current task.

For an existing branch, select `audit-existing`, fix a merge-base, create a route/node/code manifest, and load [references/existing-implementation-audit.md](references/existing-implementation-audit.md).

## Workflow

1. **Collect design evidence.** Load `figma`; fetch structured context and a same-node screenshot before coding. Capture hierarchy, constraints, tokens, copy, assets, states, navigation, account assumptions, and unknown behavior.
2. **Map the repository.** Read [references/fameex-web.md](references/fameex-web.md); inspect the route, shell, adjacent code, services, state, i18n, tests, and responsive conventions. Run the bounded reuse audit from the loaded skill root:

   ```bash
   /usr/bin/python3 <skill-root>/scripts/audit_reuse.py --repo-root <repo> <absolute-target-paths...>
   ```

   Resolve omissions with narrower batches or a reviewable higher limit. Classify controls and assets as `reuse`, `adapt`, `promote`, or `local`; explain non-reuse.
3. **Lock business contracts.** Backend contracts or PRDs own behavior, Figma owns visuals, and the repository owns structure. Never infer APIs, permissions, enums, submissions, or fallback data from Figma. For server-backed work, read [references/api-integration.md](references/api-integration.md) and complete a contract manifest for each interaction or independently releasable slice before editing that slice.
4. **Implement in slices.** Load `figma-implement-design`; use the owning component system and original assets when no shared icon fits. Put frontend-owned copy, validation, accessibility labels, and metadata in i18n. Modify only Simplified Chinese by default. Keep unconfirmed behavior unavailable and test confirmed behavior.
5. **Validate the real route.** Read [references/verification-contract.md](references/verification-contract.md), load `playwright`, and check `zh-CN`, exact viewport, responsive behavior, interactions, assets, navigation, console/network, and account-state differences. Store useful artifacts under `output-tdd/`.
6. **Validate touched scope.** Run the owning app's formatting, focused tests, typecheck, locale-path checks, and `git diff --check` from [references/fameex-web.md](references/fameex-web.md). Classify failures as introduced, pre-existing, or environmental.
7. **Report evidence.** Load `superpowers:verification-before-completion`, or its fallback, and follow the final-response contract. Never claim parity, passing checks, or completion without fresh evidence.

Code Connect is optional. Continue within confirmed scope when it is unavailable, a dependency can be bootstrapped, global checks have unrelated baseline failures, or work must be sliced. Report constraints instead of inventing behavior.
