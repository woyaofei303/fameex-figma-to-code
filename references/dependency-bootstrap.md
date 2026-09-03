# Dependency Bootstrap

Load this reference when an accepted sub-skill is missing or the current task lacks that phase's required runtime capability. For Figma, missing structured-context or screenshot tools counts even when a `figma` skill is installed.

This is an explicit repair path, not default preflight. Obtain user approval before installing a skill or plugin, starting authentication, or changing MCP/Codex configuration. Read-only inspection of current capabilities needs no approval.

Use [capability-registry.md](capability-registry.md) first to decide whether a capability is required, conditional, optional, or outside the default workflow. This file only explains recovery for a capability that has already been triggered.

## Capability Registry

```text
Capability                 Accepted available skill                         Fallback directory
Figma design evidence      figma                                            figma
Figma implementation       figma-implement-design                           figma-implement-design
Browser validation         playwright                                       playwright
Completion evidence        superpowers:verification-before-completion       verification-before-completion
                           verification-before-completion
```

An available plugin skill satisfies the dependency. Record the selected skill name, source/root, and supplied capability. If names collide, prefer the fuller current-runtime implementation; create the fallback only when no candidate qualifies. Do not create a personal duplicate merely because a plugin lives outside `$CODEX_HOME/skills`.

## Resolution Order

For each capability:

1. Check the available-skills catalog for the accepted names.
2. Check `$CODEX_HOME/skills/<fallback-name>/SKILL.md`.
3. Check known system skills and the enabled providers shown by `codex plugin list`.
4. With user approval, if an accepted official plugin provides the capability, add only that provider and verify that it is enabled.
5. If still missing, use `skill-installer` only when it resolves an exact curated or explicit GitHub source.
6. If no exact install source exists, or installation fails, run the bundled fallback bootstrap.

Do not perform a broad repository search for a similarly named skill and do not install a near-match.

## Fallback Command

Resolve `<skill-dir>` to the directory containing the active `fameex-figma-to-code/SKILL.md`, then run:

```bash
/usr/bin/python3 <skill-dir>/scripts/bootstrap_dependencies.py \
  --dependency <fallback-name> \
  --json
```

Run without `--dependency` only when all four capabilities are missing:

```bash
/usr/bin/python3 <skill-dir>/scripts/bootstrap_dependencies.py --json
```

Interpret results:

```text
present  -> validate and load the existing skill
created  -> report it, read its SKILL.md directly, and continue now
invalid  -> stop; do not overwrite the existing directory
missing:npx -> Playwright fallback was created, but browser validation remains blocked until npx exists
```

The script never overwrites an existing directory. A non-zero exit means at least one requested capability is still unsafe or unavailable.

## Same-Turn Continuation

New personal skills may not enter the runtime's automatic discovery catalog until a later turn. Do not pause solely for refresh. After any successful install or a `created` result:

1. Open `<result.path>/SKILL.md`.
2. Read it completely.
3. Follow it as the required sub-skill for the current phase.
4. Continue the original Figma-to-code task.

Direct reading applies only to a skill available on disk. A plugin or newly registered MCP server may require a catalog reload, Codex restart, or new task before its tools appear; after that refresh, reload the parent skill and resume the original task.

## Figma MCP Bootstrap

The `figma` sub-skill and the Figma MCP runtime are separate dependencies. Installing or bootstrapping the sub-skill does not register, authenticate, or hot-load an MCP server.

### Inspect before changing configuration

First inspect the Figma tools exposed to the current task, then inspect configured servers:

```bash
codex mcp list
codex mcp get <server-alias>
```

Prefer Figma's official Remote endpoint, `https://mcp.figma.com/mcp`, for link-based work. A server alias is only local; it need not be `figma`. When aliases share that endpoint, prefer an authenticated entry whose tools are callable. Another alias showing `Not logged in` is not a global failure and does not justify a duplicate. An already authenticated Desktop MCP may satisfy collection when exact-node context and screenshot tools are callable; skip remote-only probes it does not expose.

Use the same selected server for the identity probe, exact-node structured read, screenshot, and later asset calls. Do not use one alias's successful authentication as evidence for another alias.

### Register and authorize when needed

With user approval, if no official endpoint is configured, use this OAuth-first setup:

```bash
codex mcp add figmaremotemcp --url https://mcp.figma.com/mcp
codex mcp login figmaremotemcp
codex mcp list
```

`figmaremotemcp` is a collision-resistant default, not a required name. If the official endpoint already exists but is unauthenticated, run `codex mcp login <server-alias>` for that entry instead of adding another one.

OAuth is interactive. The agent may start `codex mcp login`, surface the authorization URL or browser flow immediately, and wait for the user to approve it. It must not claim that authorization completed until the command and an authenticated read both succeed. Never request, store, log, or print OAuth tokens, bearer tokens, cookies, or authorization headers.

Use a manually supplied bearer token only when the environment deliberately cannot use interactive OAuth. Follow the active `figma` skill's config reference and keep secrets in environment variables, never in the skill or task output.

### Verify the current task, not only the CLI

MCP registration or OAuth success does not prove that the current Codex task loaded the server's tools. Re-check the current task for `get_design_context` and `get_screenshot`, then use the selected server to run:

1. `whoami` when the selected server exposes it.
2. `get_design_context` for the user's exact `fileKey` and `nodeId`.
3. `get_screenshot` for the same node.

One successful context call may satisfy this preflight and Phase 2. If tools remain absent or return `unknown tool`, restart Codex or open a new task, reload the parent skill, and repeat the reads. Visual work remains blocked without structured evidence; independently evidenced non-visual repository fixes may continue only when labeled `visual audit blocked`. A screenshot, memory, or neighboring code cannot authorize visual changes.

## Validation

For every installed or bootstrapped skill:

- Confirm `SKILL.md` exists.
- Confirm frontmatter name matches the directory.
- Confirm description is non-empty.
- For Playwright, confirm `npx` is available before promising browser validation.
- For Figma, confirm an authenticated exact-node structured read and same-node screenshot in the current task. When bootstrapping Remote MCP, use the official endpoint.

## Final Reporting

Add a `Dependency Bootstrap` result to the final response when any dependency was changed:

```text
Dependency: <name>
Source: skill-installer | bundled fallback
Path: <absolute path>
Validation: <result>
Current task resumed: yes | no, with blocker
```
