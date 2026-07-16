# Exact Node Workflow

Load only for `exact-node-implementation`: a bounded page or component supplied as an exact Figma Design URL with a `node-id`.

## Entry

Use the exact node plus the current repository and worktree. Infer the owning app, route, and code target only from unambiguous repository evidence; when mapping is ambiguous, ask only for the missing target. A PRD is not required, a global Figma inventory is not required, and a Feature Manifest is not required.

Read structured context and a same-node screenshot, map the target and reuse candidates, then follow the parent workflow. Existing repository behavior and confirmed API contracts still own business behavior.

## Boundary

Do not invent API paths, permissions, states, submissions, or navigation from the design. Keep only the dependent behavior blocked when its contract is missing.

Switch to `feature-delivery` when the requested scope expands to multiple routes, product-owned states, cross-app rules, or acceptance that needs requirement-level traceability. In the new Manifest, reuse existing exact-node evidence instead of repeating verified work. Do not retroactively force a scope that stays bounded into a Feature Manifest.

## Evidence

Return the node/route/code mapping, changed files, focused tests, and real-route evidence. State unresolved business or API facts separately. Exact-node verification proves only the bounded scope; broader release claims still use the release modes.
