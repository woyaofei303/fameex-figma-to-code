---
name: figma
description: Use when a task involves a Figma Design URL, exact node-id, design context, screenshots, variables, assets, or design-to-code work and no fuller Figma skill is installed.
---

# Figma Compatibility Workflow

Use the available Figma MCP tools. Require a design URL with an exact `node-id` when using the remote server.

Installing this fallback skill does not install or authenticate the Figma MCP server. If the required tools are unavailable, authentication is unproven, or a newly registered server is not exposed to the current task, read [references/figma-mcp-config.md](references/figma-mcp-config.md) completely before continuing.

## Required Order

1. Parse `fileKey` and `nodeId` from the URL.
2. Call `get_design_context` for the exact node.
3. If the result is truncated, call `get_metadata`, identify required children, and call `get_design_context` for those child nodes.
4. Call `get_screenshot` for the same node or exact variant.
5. Fetch variables, assets, and Code Connect mappings when available.
6. Start implementation only after structured context and a screenshot exist.

Treat returned React/Tailwind as a design representation. Preserve project components, tokens, routing, state, and data patterns. Use Figma-provided assets; do not add icon packages or placeholders.

Code Connect is optional. Record entitlement failures and continue with design context and screenshots.
