# Figma MCP Configuration

Use the official remote endpoint. The preferred OAuth flow is interactive; treat server registration, authentication, and current-task tool discovery as separate checks.

## Preferred OAuth flow

Inspect existing entries first:

```bash
codex mcp list
codex mcp get <server-alias>
```

Any server alias pointing to `https://mcp.figma.com/mcp` is acceptable. If more than one exists, use an already-authenticated entry whose tools are callable; an unrelated alias showing `Not logged in` does not invalidate it.

When no official entry exists, register and log in:

```bash
codex mcp add figmaremotemcp --url https://mcp.figma.com/mcp
codex mcp login figmaremotemcp
codex mcp list
```

OAuth requires user approval in the browser or authorization URL opened by the CLI. Do not print, copy into chat, persist in this skill, or otherwise expose tokens, cookies, or authorization headers.

After login, check whether the current task exposes `get_design_context` and `get_screenshot`. Successful registration or login is not enough. Use the same selected server for `whoami`, the exact-node structured read, the same-node screenshot, and later asset calls. If the tools are absent, restart Codex or open a new task, reload the parent skill, and repeat these checks before implementation. A user-supplied screenshot does not replace the structured read or the MCP screenshot.

## Optional bearer-token fallback

Use this only in a managed non-interactive environment that deliberately supplies a bearer token. Reuse the selected server alias when one already points to the official endpoint; do not create a duplicate. In this example, replace `figmaremotemcp` with that existing alias when needed:

```toml
[mcp_servers.figmaremotemcp]
url = "https://mcp.figma.com/mcp"
bearer_token_env_var = "FIGMA_OAUTH_TOKEN"
```

Keep `FIGMA_OAUTH_TOKEN` in the environment that launches Codex. Do not print it to verify availability; use a boolean check such as:

```bash
test -n "${FIGMA_OAUTH_TOKEN:-}"
```

Restart Codex after changing configuration or the launch environment, then repeat the current-task tool and exact-node checks.
