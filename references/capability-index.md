# Capability Index

Read this compact index before work. Load the full [capability registry](capability-registry.md) at `references/capability-registry.md` only when a capability is missing or triggered and provider, installation, MCP function, or recovery detail is needed.

## Core

- `figma` plus authenticated Figma MCP: exact-node context and same-node screenshot.
- `figma-implement-design`: repository-native implementation.
- `playwright`: real-route, interaction, responsive, console, and network evidence.
- `superpowers:verification-before-completion` or fallback: fresh completion evidence.

## Triggered

- Lark PRD or embedded Sheet: `lark-doc` / `lark-sheets`.
- Missing exact dependency: `skill-installer` or bundled fallback.
- Unresolved decision: one of `grill-me` / `grill-with-docs`; then `prototype` only for a narrow experiment.
- Confirmed new or changed behavior: `tdd` or `superpowers:test-driven-development`; skip visual-only work.
- Hard, intermittent, or performance failure: `diagnosing-bugs`, `diagnose`, or `superpowers:systematic-debugging`.
- Release/branch audit: `code-review` or `review` when its two-axis workflow is needed.
- Explicit commit, push, or publish request: `github:yeet`.
- Explicit Code Connect work: `figma:figma-code-connect`.

Resolve only required or triggered capabilities. Reuse a valid provider; do not install duplicates. Installation is not completion: validate the capability, then resume the original task.
