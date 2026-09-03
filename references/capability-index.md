# Capability Index

Load a capability only when the selected mode reaches its trigger. Read the full [capability registry](capability-registry.md) at `references/capability-registry.md` only when a capability is missing or triggered and provider, MCP, or recovery detail is needed.

## Mode-required

- Figma evidence: `figma` plus an authenticated same-node context and screenshot.
- Visual implementation: `figma-implement-design`.
- Visible UI or browser audit: `playwright`.
- Completion claim: `superpowers:verification-before-completion`.

## Conditional

- Changed behavior: `tdd`; pure visual edits do not trigger it.
- Hard, intermittent, or performance failure: `diagnose`.
- Fixed-scope branch or release audit: `review`.
- Lark source: `lark-doc` / `lark-sheets`.
- Unresolved product decision: one of `grill-me` / `grill-with-docs`; narrow experiment only: `prototype`.
- Missing triggered skill: `skill-installer`, after user approval.
- Explicit Code Connect work: `figma:figma-code-connect`.

Reuse available providers. Do not install duplicates, commit, push, publish, authenticate, or change configuration unless authorized. Validate recovered capabilities, then resume the original task.
