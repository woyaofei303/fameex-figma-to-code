# Release Readiness and Post-Release Validation

Load only for `release-readiness` or `post-release-validation`. Create `docs-tdd/frontend-tasks/<feature>-release.yaml` from `assets/templates/release-readiness.yaml`. This record proves whether a fixed candidate can move from technical verification to deployment and whether the deployed version stayed healthy.

## Status language

- `not-ready`: a required slice, contract, regression, review, build, CI status, sign-off, rollout, rollback, or monitoring fact is missing or failed.
- `ready-with-known-risks`: every hard gate passed; each non-critical risk has an owner, explicit acceptance, and follow-up date.
- `ready`: all applicable hard gates passed with no open release risk.
- `released`: the candidate was deployed through the existing deployment pipeline after explicit user authorization; production verification is still pending.
- `rolled-back`: a rollback trigger fired and the recorded rollback action completed.
- `verified`: post-release evidence confirms the deployed version and observation window.

A verified slice, local route, focused test set, or clean diff does not by itself make a feature release-ready.

## Freeze the candidate

Record the fixed release commit, target environment, branch, merge-base, dirty state, included slices, excluded slices, and external dependencies. Re-run checks against that immutable commit. If code changes, replace the candidate and invalidate stale release evidence.

Every required requirement-level Traceability entry must point to verified acceptance evidence. Required server-backed work must be `verified`; `not-required` needs a reason. A `waiting`, blocked, unresolved, or guessed business interaction keeps the dependent release scope `not-ready`.

## Cross-slice regression and review

Build one cross-slice regression matrix from the Feature Manifest. Cover only affected but complete surfaces:

- Each owning app and route, with Admin and Web recorded separately.
- Required roles, account/eligibility states, permissions, active/inactive tabs, loading, error, empty, mutation, and navigation paths.
- Exact Figma viewport plus applicable repository breakpoint; `zh-CN` and required locale fallback/metadata checks.
- Confirmed API method/path/payload/response normalization, refresh behavior, duplicate/inactive queries, uploads, and error feedback.
- Analytics/acceptance events, accessibility/privacy-sensitive controls, and critical neighboring flows touched by shared code.

Use owning-package commands. For FameEX Admin, run Admin aliases/tests in the Admin package context; use the root Web configuration for Web. Separate development, integration, regression, and QA results. Repository-wide baseline noise may be recorded only after comparing with the fixed base and proving touched files are not new failures; it never waives a targeted failure.

Review the fixed diff on two independent axes:

- **Standards axis**: AGENTS/CONTRIBUTING/context/ADR and owning-app conventions.
- **Spec axis**: PRD revision, Feature Manifest Traceability, Figma states, API contracts, acceptance, and explicit user corrections.

Load `review` when available and give it the fixed point plus these sources. If it is unavailable, keep the same two result slots and perform the bounded checks directly. No unresolved P0/P1 or unowned finding may pass the gate.

## Build, CI, and sign-offs

Run the repository-established target-environment build and record the exact command plus `build_evidence`. Read the actual `ci_provider` and branch checks; record `ci_reference` and CI status rather than assuming GitHub Actions, Jenkins, or another pipeline. Do not invent a deployment command, environment name, secret, or approval path. A missing required build or inaccessible required CI result is `not-ready`.

Record applicable product sign-off, design sign-off, backend sign-off, frontend sign-off, and QA sign-off. A role may be `not-required` only with a short scope reason. Codex evidence supports a decision; it does not impersonate a human approver.

## Operational plan

Before `ready`, record:

- Release window, release owner, existing deployment pipeline, dependencies, exposure/feature-flag plan, and production-safe smoke steps.
- Each rollback trigger, measurable threshold or failure symptom, rollback action, rollback owner, and recovery verification.
- Monitoring owner, dashboards/logs/error checks, observation window, and expected analytics or business signal.

`ready-with-known-risks` is not a shortcut for missing gates. It is allowed only for accepted, non-critical risks that do not hide unresolved product behavior, privacy/security issues, failed tests, broken build/CI, or an unusable rollback.

## Deployment boundary

Production deployment is an external write. Execute it only after explicit user authorization for the target environment and only through the existing deployment pipeline discovered in the repository or organization. Record `deployment_authorization`, `authorized_by`, and `authorized_scope`. `github:yeet` may publish code when requested; it does not authorize or prove production deployment.

After deployment, record the deployed version/tag/commit, time, environment, operator/pipeline result, and status `released`. If deployment is not authorized or the pipeline is inaccessible, stop at `ready` and report the exact boundary.

## Post-release validation

Use production-safe smoke steps: default to read-only checks; run mutations only when the approved release plan explicitly permits them. Confirm the deployed version, critical routes, asset/loading health, console/network errors, applicable account states, and API response shape. Check the recorded logs, error rate, alerts, metrics, and analytics during the observation window.

Attach sanitized post-release evidence and choose `keep`, `observe`, or `rollback`. If a rollback trigger fires, execute only the authorized recorded rollback action, verify recovery, and mark `rolled-back`. Mark `verified` only after the observation window and all required smoke, monitoring, and acceptance signals pass.

## Exit evidence

The release record must identify what was checked, by whom or by which pipeline, against which commit/environment, with exact evidence and unresolved risks. Keep status `not-ready` whenever a required fact is missing; absence of a detected problem is not proof of readiness.
