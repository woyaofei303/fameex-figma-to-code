# Product-to-Code Delivery

Load this reference only for `feature-delivery` or `slice-implementation`. It connects product requirements, Figma, repository code, API integration, and acceptance without loading extra tools on ordinary page work.

## Start with the whole feature

For the first pass, provide the product document, the global Figma root, repository, and branch. Do not ask the user to paste every frame one by one.

1. Read the main PRD and every relevant embedded Sheet or linked document. Record title, URL/token, revision, scope, states, permissions, analytics, acceptance, and unresolved decisions.
2. Treat missing permission as a visible blocker for only the affected facts. Record the inaccessible source; do not guess from screenshots or old code.
3. Use the global Figma root for discovery: inventory pages, states, dialogs, mobile/desktop variants, and exact node IDs. A canvas or section is not an exact implementation node.
4. Read design context and screenshot for each exact implementation node selected for the next slice.
5. Map routes, apps, existing components, services, i18n, tests, and likely ownership in the repository.

Authority is explicit: product and backend contracts own behavior; Figma owns visual intent; the repository owns implementation structure; a real payload or user correction overrides earlier assumptions. Record conflicts before coding.

## Feature Manifest

Create `docs-tdd/frontend-tasks/<feature>-manifest.yaml` from `assets/templates/feature-manifest.yaml`. Keep a Traceability entry for every requirement: PRD source/revision, exact Figma state, app/route, API status, code target, acceptance, evidence, status, and blocker.

Split work by independently verifiable **business slice**, not by screenshot. One slice may contain one route, several visible states, dialogs, APIs, analytics, and tests. The manifest lets later tasks load only the active slice instead of rereading the whole PRD and design file.

API status is one of `not-required`, `waiting`, `documented`, `integrated`, or `verified`. With no confirmed API, implement only confirmed presentation/view-model behavior. Test fixtures and prototypes may use local data; production code must not use mock data, false success, or another production fallback.

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

## Slice gate

A slice enters implementation only when these are recorded:

1. Requirement and acceptance source.
2. Exact Figma nodes for every visible state being implemented.
3. Owning app, route, and reuse candidates.
4. API status plus contract manifest when server-backed.
5. Product/Figma/code conflicts and their resolution or blocker.

Then implement, verify the real route and network behavior, map tests/evidence back to acceptance, and update the Feature Manifest. A blocked slice stays blocked; confirmed sibling slices continue.

## Compact flow

```text
PRD and linked sources -> global Figma inventory -> repository map
-> Feature Manifest -> business slices -> contract/API gate
-> implementation -> browser/network/tests -> acceptance evidence
```
