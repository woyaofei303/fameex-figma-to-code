---
name: playwright
description: Use when terminal-driven browser navigation, snapshots, element interaction, screenshots, traces, or local UI validation is required and no fuller Playwright skill is installed.
---

# Playwright CLI Compatibility Workflow

Require `npx` before promising browser validation:

```bash
command -v npx >/dev/null 2>&1
```

Use the CLI directly when no wrapper exists:

```bash
npx --yes --package @playwright/cli playwright-cli open <url> --headed
npx --yes --package @playwright/cli playwright-cli snapshot
```

## Required Loop

1. Open the target local URL.
2. Take a fresh snapshot before referencing elements.
3. Interact using references from the latest snapshot.
4. Re-snapshot after navigation, modal/menu changes, or substantial DOM updates.
5. Capture desktop, applicable mobile, and failure evidence.

Store generated artifacts only under:

```text
output-tdd/playwright/<task-timestamp>/
```

Exercise only behavior established by Figma, a PRD/backend contract, existing product behavior, or explicit user instruction. Report failed steps with artifacts and likely code locations.
