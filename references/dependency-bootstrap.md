# Dependency Bootstrap

Load this reference before the first required sub-skill and whenever a later phase reports that its sub-skill is unavailable.

## Capability Registry

```text
Capability                 Accepted available skill                         Fallback directory
Figma design evidence      figma                                            figma
Figma implementation       figma-implement-design                           figma-implement-design
Browser validation         playwright                                       playwright
Completion evidence        superpowers:verification-before-completion       verification-before-completion
                           verification-before-completion
```

An available plugin skill satisfies the dependency. Do not create a personal duplicate merely because it is not under `$CODEX_HOME/skills`.

## Resolution Order

For each capability:

1. Check the available-skills catalog for the accepted names.
2. Check `$CODEX_HOME/skills/<fallback-name>/SKILL.md`.
3. Check known system and plugin skills surfaced by the current runtime.
4. If still missing, use `skill-installer` only when it resolves an exact curated or explicit GitHub source.
5. If no exact install source exists, or installation fails, run the bundled fallback bootstrap.

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

New personal skills may not enter the runtime's automatic discovery catalog until a later turn. Do not pause solely for refresh. After a `created` result:

1. Open `<result.path>/SKILL.md`.
2. Read it completely.
3. Follow it as the required sub-skill for the current phase.
4. Continue the original Figma-to-code task.

## Validation

For every installed or bootstrapped skill:

- Confirm `SKILL.md` exists.
- Confirm frontmatter name matches the directory.
- Confirm description is non-empty.
- For Playwright, confirm `npx` is available before promising browser validation.
- For Figma, confirm the Remote MCP with an authenticated read call before design extraction.

## Final Reporting

Add a `Dependency Bootstrap` result to the final response when any dependency was changed:

```text
Dependency: <name>
Source: skill-installer | bundled fallback
Path: <absolute path>
Validation: <result>
Current task resumed: yes | no, with blocker
```
