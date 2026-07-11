# Browser Validation and Completion Contract

Load this reference before starting Playwright and again before the final response.

## Artifact Contract

Create one task-scoped directory:

```text
output-tdd/playwright/<task-timestamp>/
```

Store only artifacts useful for review:

- Desktop screenshot at the Figma frame width or closest supported viewport.
- Mobile screenshot when a mobile frame or existing mobile behavior applies.
- Failure screenshots named for the failed step.
- Trace output when an interaction failure cannot be explained from a snapshot and screenshot.

Keep all generated runtime artifacts under `output-tdd/`. Do not create another top-level artifact directory. Do not add persistent Playwright test files unless the user requests them or the change introduces behavior that needs regression coverage.

## Browser Validation Sequence

1. Confirm the target local URL and owning app are running.
2. Open the page with the Playwright CLI wrapper.
3. Take a snapshot before referencing elements.
4. Check page shell, section order, visible copy, assets, and overflow.
5. Check spacing, alignment, sizing, typography, colors, borders, radii, and clipping against the Figma screenshot.
6. Exercise confirmed buttons, tabs, menus, forms, and modals.
7. Re-snapshot after navigation or material DOM changes.
8. Capture desktop and applicable mobile screenshots.
9. Inspect console or interaction errors when the workflow exposes them.
10. Re-run the affected step after each fix.

If Figma provides only one viewport, validate that viewport exactly. Use existing project breakpoints for an additional responsive smoke check and report that the responsive expectation came from repository behavior rather than a missing Figma frame.

## Interaction Boundary

Exercise behavior only when established by at least one of:

- The selected Figma state or annotation.
- A PRD or backend contract.
- Existing behavior on the target page.
- An explicit user instruction.

Do not invent submissions, redirects, API calls, permission checks, or mock fallbacks. Record unresolved behavior in the final report.

## Failure Record

For every unresolved failure, report:

```text
Step: <browser action or visual check>
Expected: <evidence-based expectation>
Actual: <observed result>
Artifact: <absolute screenshot or trace path>
Likely code locations:
- <absolute file path>
Reasoning: <short evidence-based mapping>
```

Do not report a vague “visual mismatch” without an artifact and likely code location.

## Final Response Contract

Return these sections in order.

### Outcome

State what was implemented and whether browser validation completed. Do not claim parity when it did not run.

### Figma Mapping

List the selected node and its implemented page sections or components.

### Reused Project Code

List reused components, hooks, tokens, icons, services, and state patterns.

### 修改文件

Provide every changed absolute file path in a copyable fenced block.

### Validation

Report the exact command or browser step and result for:

- Biome on touched files.
- Owning-package typecheck.
- Focused tests when relevant.
- `git diff --check`.
- Playwright desktop.
- Playwright mobile when applicable.
- Confirmed key interactions.

Classify non-passing results as introduced, pre-existing, or environmental.

### Artifacts

Provide absolute paths to screenshots and traces.

### Failures and Deviations

Use the failure-record shape above. State `None` only when evidence supports it.

### Pending Business Questions

List behavior Figma and repository evidence could not establish. Keep it out of speculative implementation code.

### 查看修改

Provide standalone commands without shell prompts:

```bash
git status --short
git diff -- <touched-paths...>
```

## Completion Gate

Before claiming completion, verify that:

- Structured Figma context and screenshot were fetched before implementation.
- The real repository was mapped before new components were created.
- No business behavior was guessed.
- Browser evidence exists or the concrete browser blocker is reported.
- Every changed file is listed.
- Fresh validation output supports every pass claim.
