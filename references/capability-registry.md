# Capability Registry

This registry tells the parent skill what each dependency does, when it is needed, and how to recover when it is absent. Resolve only a **required or triggered** capability. A similar name, a cached plugin, an MCP login, or an installed file is not enough; validate the capability in the current task.

## Contents

- [Classification](#classification)
- [Plugin Providers](#plugin-providers)
- [Figma MCP Function Catalog](#figma-mcp-function-catalog)
- [Missing Capability Recovery](#missing-capability-recovery)

## Classification

### Required

- `figma`: reads the exact design node, screenshot, variables, and original assets. Its Figma MCP runtime is a separate requirement.
- `figma-implement-design`: translates verified design evidence into the owning repository without replacing its component system.
- `playwright`: opens the real route and verifies layout, interaction, navigation, console, network, and responsive behavior.
- `superpowers:verification-before-completion` or `verification-before-completion`: requires fresh command and browser evidence before completion claims.

An available skill from a personal directory, system bundle, or enabled plugin may satisfy the capability. Record the selected skill name and source; do not install a duplicate merely to obtain another copy.

### Conditional

- `skill-installer`: use only when a required or triggered skill is missing and an exact curated or GitHub source is known.
- `lark-doc` and `lark-sheets`: use for supplied Lark requirements and embedded Sheets; unresolved access blocks only dependent facts.
- `grill-me`: use only when evidence cannot resolve a product decision and an interactive interview is needed.
- `grill-with-docs`: use instead when repository context/glossary/ADR documents materially constrain that decision.
- `prototype`: use only for a narrow unresolved logic or visual question; clean it up before production work.
- `tdd` or `superpowers:test-driven-development`: use for confirmed new or changed behavior after recording its test seam. Select one provider; visual-only work does not trigger TDD.
- `diagnosing-bugs`, `diagnose`, or `superpowers:systematic-debugging`: use for a hard, intermittent, or performance failure after a focused check exposes the symptom. Select one provider; an ordinary Figma mismatch does not trigger diagnosis.
- `code-review` or `review`: use for a fixed-commit branch or release audit when Standards and Spec must be checked separately. Select one provider and pass the fixed point plus the known spec sources.
- `github:yeet`: use only when the user explicitly asks to commit, push, or publish the finished changes.

### Optional

- `figma:figma-code-connect`: use only when the user explicitly asks to create or maintain Code Connect mappings. It normally requires a published team-library component and a supported Figma Organization or Enterprise plan.
- Existing read-only Code Connect mappings may help select repository components, but missing mappings never block normal Figma-to-code work.

### Not used by default

- `browser` / `chrome` / `computer-use` do not replace Playwright route evidence or Figma MCP design evidence.
- `imagegen` must not recreate assets that Figma already exposes.
- web search must not replace the supplied Figma node, PRD, API contract, or repository evidence.
- Unrelated plugins and Apps/Connectors are not installed speculatively. **No App or Connector is mandatory** for the normal workflow.

## Plugin Providers

A capability is the dependency; a plugin is only one possible provider. Check enabled plugins before adding one:

```bash
codex plugin list
```

The official Figma plugin, `figma@openai-curated`, can provide the Figma skills and MCP integration:

```bash
codex plugin add figma@openai-curated
```

The Superpowers plugin, `superpowers@openai-curated`, can provide completion verification and conditional TDD or diagnosis providers:

```bash
codex plugin add superpowers@openai-curated
```

Do not add a plugin when the accepted capability is already available. After adding one, confirm that it is enabled and that its skill appears in the current catalog. A cached directory alone does not prove installation.

## Figma MCP Function Catalog

The active `figma` skill owns exact tool names and arguments. Use the smallest set needed for the current work.

### Normal implementation

- `whoami`: confirm the selected server identity when the server exposes it.
- `get_design_context`: required structured read for the user's exact `fileKey` and `nodeId`.
- `get_screenshot`: required visual evidence for the same node.
- `get_metadata`: use when the target is too large, context is incomplete, or child-node discovery is needed.
- `get_variable_defs`: use when tokens or variable values are not present in design context.
- Figma asset URLs returned by MCP: use original icons and images instead of redrawing them; do not invent a placeholder when retrieval fails.
- `get_code_connect_map`: read existing component mappings when exposed and useful for reuse.

### Code Connect only

- `get_code_connect_suggestions`: find Figma components that may need mappings.
- `get_context_for_code_connect`: retrieve the component props and repository context needed for a `.figma.ts` mapping.
- `add_code_connect_map`: writes a mapping in Figma. Use it only after an **explicit user request** authorizes that external write.

### Outside the default page workflow

- `get_figjam`: FigJam inspection, not normal Design-node implementation.
- `create_design_system_rules`: generating repository design-system instructions, not implementing one page.
- `get_strategy_for_mapping` and `send_get_strategy_response`: local/alpha Code Connect mapping workflow; use only when the loaded Code Connect skill explicitly requires them.

Tool exposure varies by Figma MCP implementation. Do not claim a missing optional tool is a failure when the required exact-node context and screenshot calls succeed.

## Missing Capability Recovery

Follow this order:

1. Check the current available-skills catalog and read the accepted `SKILL.md` completely.
2. Check the personal skill path and `codex plugin list`; reuse any valid provider already available.
3. If an exact source is known, load `skill-installer` and install only that missing skill or official plugin.
4. If the four core skills still have no exact provider, use `scripts/bootstrap_dependencies.py` as described in [dependency-bootstrap.md](dependency-bootstrap.md).
5. Configure Figma MCP separately, validate the exact node, then continue the phase that was waiting.

**Do not install optional or unrelated capabilities** just because they appear in this registry.

### Figma plugin and MCP

If neither the accepted Figma skill nor its provider is present, add the official plugin. If the official endpoint is not configured, add and authorize it:

```bash
codex plugin add figma@openai-curated
codex mcp add figmaremotemcp --url https://mcp.figma.com/mcp
codex mcp login figmaremotemcp
codex mcp list
```

OAuth requires the user's browser approval. After login, the current task must still call the exact-node context and screenshot functions successfully.

### Lark PRD

When a supplied requirement is a Lark URL and `lark-doc` is unavailable, install the official Lark CLI skills, verify the skill file and CLI, then fetch with the identity requested by the user or permitted by the document:

```bash
npx skills add larksuite/cli -g -y
lark-cli --help
```

If authentication or document permission still fails, block only the PRD-dependent decisions and report the exact boundary.

### Same-task continuation

After installing a skill, **Read the installed `SKILL.md`** completely and use it in the current turn. After adding a plugin or MCP server, reload the parent skill and capability manifest. If new tools are not exposed, **restart Codex or open a new task**, reload this skill, and repeat the runtime checks. Then **resume the original task** at the phase that was waiting; do not end at “installation succeeded.”

If `npx` is missing, install a supported Node.js/npm runtime only within the user's authorized machine scope, verify `npx`, and rerun the Playwright check. Ask before a system-level change that needs new authority.
