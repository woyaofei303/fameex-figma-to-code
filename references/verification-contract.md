# Browser Validation and Completion Contract

Load before Playwright and again before the final response. This file is the single browser checklist.

## Artifacts

Create one task-scoped directory:

```text
output-tdd/playwright/<task-timestamp>/
```

Keep only useful review evidence: desktop screenshot at the Figma width, applicable mobile screenshot, failure screenshots named by step, and a trace only when snapshots cannot explain an interaction failure. Keep runtime artifacts under `output-tdd/`; add persistent Playwright tests only for behavior needing regression coverage or when requested.

## Browser Checklist

1. Confirm the owning app and exact local route are running.
2. Open the route with the Playwright CLI wrapper and take a fresh snapshot before referencing elements.
3. At the exact Figma viewport, compare shell, section order, copy, assets, overflow, spacing, alignment, sizing, typography, colors, borders, radii, and clipping with the node screenshot.
4. Confirm images have non-zero natural dimensions; inspect broken, translucent, cropped, or unexpectedly large assets.
5. Exercise only interactions established by Figma, PRD/backend contract, existing behavior, or explicit user instruction. Check focus, keyboard, disabled, loading, validation, and feedback states when applicable.
6. Verify each exercised link in the current branch; otherwise record it as a dependency.
7. Re-snapshot after navigation or material DOM changes. Inspect console/network errors exposed by the workflow.
8. Load `zh-CN`; check raw keys, fallback copy, validation text, metadata, accessibility labels, truncation, overlap, and horizontal overflow. Check another locale only when its translated resource already exists or is explicitly in scope.
9. Capture desktop and applicable mobile evidence. If Figma has one viewport, use it exactly and add one repository-breakpoint smoke check, clearly labeling that responsive expectation as repository-derived.
10. Re-run each affected step after a fix.

When local authentication or eligibility differs from the Figma state, state the difference. Never treat sample account values or an unlocked design state as backend validation.

## Business Boundary

Do not invent submissions, redirects, API calls, permissions, eligibility, enums, or mock fallbacks. Exercise behavior only when established by selected-node evidence, a PRD/backend contract, existing target behavior, or an explicit instruction. Report unresolved behavior instead of implementing it speculatively.

## Failure Record

For each unresolved failure, report:

```text
Step: <browser action or visual check>
Expected: <evidence-based expectation>
Actual: <observed result>
Artifact: <absolute screenshot or trace path>
Likely code locations:
- <absolute file path>
Reasoning: <short evidence-based mapping>
```

Do not report a vague mismatch without an artifact and likely code location.

## Final Response Contract

Return these sections in order:

1. **Outcome** — implemented scope and whether browser validation completed; no parity claim without evidence.
2. **Figma Mapping** — file/node and implemented sections/components.
3. **Reuse Decisions** — reused/adapted/promoted/local components and assets, with reasons for non-reuse; list shared hooks, tokens, icons, services, and state patterns.
4. **修改文件** — every changed absolute path in a copyable fenced block.
5. **Validation** — exact command/step and result for Biome, owning-app typecheck, focused tests, Simplified Chinese JSON and lookup coverage, localized metadata, `git diff --check`, Playwright desktop/mobile, and confirmed interactions. Include other-locale evidence only when in scope. Classify failures as introduced, pre-existing, or environmental.
6. **Artifacts** — absolute screenshot/trace paths.
7. **Failures and Deviations** — failure-record shape; `None` only when evidence supports it.
8. **Pending Business Questions** — behavior not established by Figma and repository evidence.
9. **查看修改** — standalone `git status --short` and touched-path `git diff` commands.

## Completion Gate

Before claiming completion, verify:

- Structured Figma context and the matching node screenshot preceded implementation.
- The real route and owning app were mapped; the manifest classified controls/assets as `reuse`, `adapt`, `promote`, or `local`.
- The owning component system was preferred; any local control has a recorded behavior/complexity reason.
- Existing icons were checked; a missing icon uses the Figma original or was promoted to `packages/icon` only when semantically reusable.
- No business behavior was guessed; route targets and account assumptions were validated or reported.
- Frontend-owned copy, validation, accessibility labels, and metadata use i18n; Simplified Chinese source keys are complete; no other-language files were generated unless explicitly requested.
- Exact-viewport and responsive evidence exists, or the concrete browser blocker is reported.
- Every changed file is listed and fresh output supports every pass claim.
