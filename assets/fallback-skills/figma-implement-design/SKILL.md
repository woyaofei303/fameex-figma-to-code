---
name: figma-implement-design
description: Use when implementing repository UI from a Figma node after design context and a screenshot have been collected and no fuller Figma implementation skill is installed.
---

# Figma Implementation Compatibility Workflow

Translate confirmed Figma evidence into the existing repository architecture.

## Implementation Gate

Do not edit UI code until the exact node's structured context and screenshot are available.

## Repository Mapping

1. Resolve the existing route or component.
2. Inspect adjacent feature code, shared UI, icons, services, state, localization, and tests.
3. Reuse matching components, hooks, tokens, and assets before creating new code.
4. Prefer adapting an existing page over adding a parallel route.

Use PRDs and backend contracts for business behavior, Figma for visual and interaction intent, and repository conventions for implementation structure. Do not invent endpoints, fields, permissions, submissions, redirects, or fallback data.

Implement large frames in independently verifiable slices. Validate each slice against the Figma screenshot and preserve unrelated user changes.
