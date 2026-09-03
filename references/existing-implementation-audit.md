# Existing Implementation Audit

## Entry Contract

Fix source head and merge-base; record worktree, dirty state, route, exact node, viewport, account assumptions, code paths, and branch-only dependencies.

## Delta-First Loop

Read merge-base-to-HEAD name/stat output once, then one route slice. Review before editing. Fetch one exact-node context and screenshot, run one bounded reuse audit, compare the real route, classify findings, fix supported issues only, validate, and independently review.

## Finding Classes

Use code issue, PR-specific dependency, reusable Skill gap, or no action. For every finding, record evidence, class, disposition (`keep`, `fix`, or `defer`), reason, and verification status. Retain supported deferred findings. Record visual, interaction, component reuse, icon/artwork, i18n, accessibility/privacy, and business/route evidence separately.

## Artifacts

Maintain a manifest, one route report per slice, a Skill gap log, and browser evidence paths. Reuse evidence by node ID.

## No-Op and Blocked Evidence

For a no-op, record the inspection scope and evidence supporting no modification. For a blocked audit, record attempted steps, the failed or missing prerequisite, and existing evidence paths; do not record only the conclusion.

## Stop and Continue Conditions

Visual work remains blocked without structured exact-node evidence. Independently evidenced non-visual repository fixes may continue, but label `visual audit blocked`. Do not invent business behavior.

## Token Controls

Never load the full PR diff. Use one page per agent context, split bounded audit paths when candidates are omitted, avoid full DOM dumps and traces by default, and promote a new script only after the same deterministic step recurs twice.
