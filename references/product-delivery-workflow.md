# Product-to-Code Delivery

Load this reference only for `feature-delivery` or `slice-implementation`. It connects product requirements, Figma, repository code, API integration, and acceptance without loading extra tools on ordinary page work.

## Start with the whole feature

For the first pass, provide the product document, the global Figma root, repository, and branch. Do not ask the user to paste every frame one by one.

1. Read the main PRD and every relevant embedded Sheet or linked document. Record title, URL/token, revision, scope, states, permissions, analytics, acceptance, and unresolved decisions.
2. Treat missing permission as a visible blocker for only the affected facts. Record the inaccessible source; do not guess from screenshots or old code.
3. Use the global Figma root for discovery: inventory pages, states, dialogs, mobile/desktop variants, and exact node IDs. A canvas or section is not an exact implementation node.
4. Read design context and screenshot for each exact implementation node selected for the next slice.
5. Map routes, apps, existing components, services, i18n, tests, and likely ownership in the repository.
6. Only when the user mentions prior work, rework, or an existing requirement,
   search direct-user history with the bounded, read-only helper:

   ```bash
   /usr/bin/python3 <skill-root>/scripts/search_codex_history.py \
     --ticket <ticket> \
     --route <route> \
     --since <YYYY-MM-DD> \
     --limit 50 \
     --json
   ```

   Search by the exact ticket and route; add repeatable `--term` values for a
   branch, API, or file. Inspect relevant Git commits and generated task files;
   treat excerpts as leads and verify drift-prone facts against the current repository.
   Never persist raw sessions in the feature repository.

Authority is explicit: product and backend contracts own behavior; Figma owns visual intent; the repository owns implementation structure; a real payload or user correction overrides earlier assumptions. Record conflicts before coding.

## Feature Manifest

Create `docs-tdd/frontend-tasks/<feature>-manifest.yaml` from
`assets/templates/feature-manifest.yaml`. Copy
`assets/templates/visual-evidence.json` to
`output-tdd/figma-audits/<task>/visual-evidence.json` and reference that path
from `visual_evidence`; feature and exact-node modes use the same visual
schema. Fill `required_viewports` from exact frames, repository boundaries, and
user corrections; keep sourced expected/actual sizing rows for changed layout
owners. Record product, Figma, API, repository, and bounded local history
sources. Keep one Traceability entry per requirement: `requirement_status`,
source/revision, exact Figma state, app/route, API, analytics, code target,
acceptance, evidence, and blocker. Record each slice's public test seam for
confirmed behavior, or `not-required` for visual-only work. A slice summary
does not replace requirement-level traceability.

Split work by independently verifiable **business slice**, not by screenshot. One slice may contain one route, several visible states, dialogs, APIs, analytics, and tests. The manifest lets later tasks load only the active slice instead of rereading the whole PRD and design file.

API status is one of `not-required`, `waiting`, `documented`, `integrated`, or `verified`. With no confirmed API, split out only an independently verifiable presentation/view-model sub-slice. The dependent work remains `waiting` and does not enter implementation. Test fixtures and prototypes may use local data; production code must not use mock data, false success, or another production fallback.

When a feature spans configuration and consumption, complete Admin before Web if Admin defines data or rules consumed by Web. Independent slices may proceed in parallel only when their contracts do not depend on each other.

## Decision tools: conditional, not a chain

Inspect the PRD, Figma, code, and contracts first. Do not load any decision skill when evidence already answers the question.

- Load **one interview mode** only when a real product or architecture choice remains and user input is needed.
  - `grill-me`: use for an undocumented plan or decision tree. Ask one question at a time and include a recommended answer.
  - `grill-with-docs`: use instead when `CONTEXT.md`, `CONTEXT-MAP.md`, or relevant ADRs exist and terminology or a durable decision must be checked against them. Create glossary/ADR content only when that skill's threshold is met.
- Load `prototype` only after the open question is narrow and a runnable experiment will change the decision.
  - Use a logic prototype for UI state priority, transition, or data-shape questions—not to invent backend-owned business rules.
  - Use a UI prototype only when appearance is genuinely undecided. Skip it when an exact Figma node already decides the layout.
  - Keep it isolated and throwaway; capture the answer, then delete or absorb it before production implementation. Real code still follows normal tests and verification.

These tools do not run automatically, do not run together by default, and are not prerequisites. Their purpose is to resolve a specific uncertainty, not add ceremony or token cost.

## Lifecycle and ownership

Track Web, Admin, integration, and QA separately when they have different owners or evidence. For each requirement and slice, record four gates:

- `development`: code and focused tests are complete in the owning app.
- `integration`: the confirmed API contract and real-session network behavior are verified, or `not-required`.
- `regression`: affected routes, states, apps, and acceptance items pass cross-slice review.
- `release`: the fixed candidate commit passes [release readiness](release-readiness.md) and has an authorized deployment plan.

Moving one gate forward never implies the next gate passed. Admin precedes Web when Web consumes Admin-configured rules; otherwise keep the tracks independent.

## Slice gate

A slice enters implementation only when these are recorded:

1. Requirement and acceptance source.
2. Exact Figma nodes for every visible state being implemented.
3. Owning app, route, and reuse candidates.
4. API status plus contract manifest when server-backed.
5. Product/Figma/code conflicts and their resolution or blocker.
6. Public test seam for confirmed new or changed behavior, or `not-required` for visual-only work.

Then implement, verify the real route and network behavior, map tests/evidence back to acceptance, and update the Feature Manifest. A blocked slice stays blocked; confirmed sibling slices continue. When all required slices reach regression, enter `release-readiness`; after an explicitly authorized deployment, enter `post-release-validation`.

Before marking visual evidence passed, run:

```bash
/usr/bin/python3 <skill-root>/scripts/validate_visual_evidence.py \
  --manifest output-tdd/figma-audits/<task>/visual-evidence.json \
  --repo-root <repo>
```

An unresolved API can coexist with a verified presentation slice, but the
validator rejects a complete-function or release claim until that contract is
resolved.

## Compact flow

```text
PRD and linked sources -> global Figma inventory -> repository map
-> Feature Manifest -> business slices -> contract/API gate
-> implementation -> integration -> cross-slice regression and review
-> release readiness -> authorized deployment -> post-release evidence
```
