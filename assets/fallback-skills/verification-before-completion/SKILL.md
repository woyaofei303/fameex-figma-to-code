---
name: verification-before-completion
description: Use before claiming work is complete, fixed, visually matched, tested, or passing when no fuller verification-before-completion skill is installed.
---

# Verification Before Completion Compatibility Gate

Never make a completion or pass claim without fresh evidence from the current run.

Before reporting:

1. Identify the command or browser step that proves each claim.
2. Run it completely.
3. Read the exit code, failures, warnings, screenshots, and traces.
4. Classify failures as introduced, pre-existing, or environmental.
5. State the actual result and concrete blockers.

Tests do not prove a build, formatting does not prove types, and code changes do not prove visual parity. If browser validation did not run, say so and do not claim 1:1 parity.
