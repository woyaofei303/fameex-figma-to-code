# Capability Registry

Use this registry only after the compact index routes here. Resolve the capability needed by the current mode; availability is not a reason to invoke a tool.

## Classification

### Mode-required

- `figma`: required only when Figma evidence is supplied; use authenticated exact-node structure and a same-node screenshot.
- `figma-implement-design`: required for visual implementation.
- `playwright`: required for visible UI changes or an explicit browser audit.
- `superpowers:verification-before-completion`: required before a completion claim.

An already available personal, system, or plugin skill may satisfy the capability. Do not install a duplicate provider.

### Conditional

- `skill-installer`: only for a missing triggered skill with an exact source, after approval.
- `lark-doc` / `lark-sheets`: supplied Lark requirements or embedded Sheets.
- `grill-me` / `grill-with-docs`: unresolved product decisions; select one.
- `prototype`: one narrow experiment whose result is deleted or absorbed.
- `tdd`: confirmed new or changed behavior; visual-only work does not trigger it.
- `diagnose`: hard, intermittent, or performance failures after a focused check reproduces the symptom.
- `review`: fixed-scope branch or release audits.

### Optional

- `figma:figma-code-connect`: only for an explicit Code Connect request. Read-only existing mappings may help reuse; missing mappings do not block page work.

### Not used by default

- `browser` / `chrome` / `computer-use` do not replace Playwright or Figma evidence.
- `imagegen` does not recreate assets already available from Figma.
- web search does not replace supplied Figma, product, API, or repository evidence.
- Unrelated plugins and Apps/Connectors are not installed speculatively. **No App or Connector is mandatory** for this workflow.

## Figma MCP Function Catalog

Use the smallest set supported by the selected Figma provider.

### Normal Figma work

- `whoami`: inspect identity when exposed.
- `get_design_context`: structured context for the exact `fileKey` and `nodeId`.
- `get_screenshot`: visual evidence for the same node.
- `get_metadata`: large-node discovery or incomplete context.
- `get_variable_defs`: missing token values.
- Figma asset URLs: retrieve original assets instead of redrawing them. If retrieval fails, use a temporary placeholder only when the user permits iterative work; mark it pending and do not claim exact visual completion.
- `get_code_connect_map`: inspect an existing mapping when useful.

### Explicit Code Connect work

- `get_code_connect_suggestions`
- `get_context_for_code_connect`
- `add_code_connect_map`: external write; requires an **explicit user request**.

### Outside normal page work

- `get_figjam`
- `create_design_system_rules`
- `get_strategy_for_mapping`
- `send_get_strategy_response`

Missing optional functions are not failures when exact-node context and screenshot reads succeed.

## Missing Capability Recovery

First inspect the current skill catalog, personal skill directory, and enabled providers:

```bash
codex plugin list
```

If a triggered capability is still absent, **ask for user approval before installing** a skill or plugin, starting authentication, or changing MCP/Codex configuration. Approval for one action does not authorize unrelated dependencies.

After approval, use the smallest applicable recovery:

1. Load `skill-installer` for an exact curated or user-specified source.
2. Add the official Figma provider only when no accepted provider exists:

   ```bash
   codex plugin add figma@openai-curated
   ```

3. Use `scripts/bootstrap_dependencies.py` only when no exact install source works, as described in [dependency-bootstrap.md](dependency-bootstrap.md).
4. Configure the official Figma endpoint only when exact-node tools remain unavailable:

   ```bash
   codex mcp add figmaremotemcp --url https://mcp.figma.com/mcp
   codex mcp login figmaremotemcp
   codex mcp list
   ```

5. For an approved Lark skill install:

   ```bash
   npx skills add larksuite/cli -g -y
   lark-cli --help
   ```

**Do not install optional or unrelated capabilities.** After installation, **Read the installed `SKILL.md`** completely. A plugin or MCP change may require **restart Codex or open a new task** before tools appear. Validate the capability, reload this skill, and **resume the original task** rather than stopping at installation success.
