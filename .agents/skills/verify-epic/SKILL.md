---
name: verify-epic
description: Run full QA for an epic — unit/integration/functional tests filtered to epic scope, then Playwright e2e click-through. Accepts an optional --screenshots flag to capture screenshots into e2e/screenshots/. Use when the user runs `/verify-epic <epic name or number> [--screenshots]` or when called from implement-epic as the final QA gate.
argument-hint: <epic name or number> [--screenshots]
disable-model-invocation: true
allowed-tools: Read Write Edit Bash Glob Grep
---

# verify-epic — full QA gate for an epic

You are running the `verify-epic` skill. Input: `$ARGUMENTS` — the epic name or number, optionally followed by `--screenshots`.

## 0. Parse arguments

Split `$ARGUMENTS` into:
- **epic ref** — the first token (number or slug/title).
- **screenshots flag** — `true` if `--screenshots` appears anywhere in the arguments, `false` otherwise.

## 1. Resolve the epic

1. If the epic ref is a number → glob `specs/<num>_*.md`, pick the PRD (no `-spec`) and its `-spec.md` sibling if present.
2. If the epic ref is a slug/title → fuzzy-match against `specs/*.md`.
3. **If no PRD matches → STOP.** Tell the user: "No PRD found for `<arg>` in `specs/`. Run `/brainstorm <epic>` first."
4. Read the PRD and tech spec (if present), `specs/briefing.md`, and `specs/roadmap.md` if they exist.
5. From the PRD, extract the **slug** (the `<slug>` part of `specs/<num>_<slug>.md`) and any domain keywords (module names, feature names, file path fragments) that identify this epic's code.

## 2. Identify test scope

Scan the project for test files relevant to this epic:
- Glob all `**/*.test.{ts,tsx,js,jsx}` and `**/*.spec.{ts,tsx,js,jsx}` (excluding `node_modules`).
- A test file is **in scope** if its path or content references any of the epic's domain keywords.
- List the in-scope test files. If none are found, note that no unit/integration tests exist yet for this epic.

## 3. Run unit / integration / functional tests

Run vitest filtered to the in-scope test files:

```
npx vitest run <file1> <file2> ...
```

If no in-scope files were found, run the full suite as a baseline:

```
npm test
```

Capture stdout/stderr. Record pass/fail counts.

## 4. Playwright e2e click-through

### 4a. Check for Playwright

Check whether `@playwright/test` is installed:
```
npx playwright --version 2>/dev/null
```

If not installed, install it non-interactively and install browsers:
```
npm install --save-dev @playwright/test
npx playwright install --with-deps chromium
```

### 4b. Locate or create e2e tests

- Check for existing e2e tests in `e2e/` that mention the epic slug or domain keywords.
- If none exist, create a minimal click-through test at `e2e/<slug>.spec.ts` that:
  - Navigates to the epic's primary route(s) (derived from the PRD or tech spec).
  - Asserts the key UI elements load without JS errors.
  - Performs the main happy-path user interaction described in the PRD.

### 4c. Configure screenshots (conditional)

If the screenshots flag is `true`:
- Ensure `e2e/screenshots/` directory exists (`mkdir -p e2e/screenshots`).
- In the e2e test, add `await page.screenshot({ path: 'e2e/screenshots/<slug>-<step>.png' })` after each major interaction step.
- Pass `--output=e2e/screenshots` to the Playwright CLI.

### 4d. Run Playwright

Start the dev server in the background, wait for it to be ready, then run:

```
# Start dev server
npm run dev &
DEV_PID=$!

# Wait for ready
npx wait-on http://localhost:3000 --timeout 60000

# Run e2e
npx playwright test e2e/<slug>.spec.ts --reporter=list

# Stop dev server
kill $DEV_PID
```

If `wait-on` is not available, use a polling loop:
```
for i in $(seq 1 30); do curl -sf http://localhost:3000 && break || sleep 2; done
```

Capture Playwright output verbatim.

## 5. Fix failures

For each failing test (unit or e2e):
- Diagnose root cause: test bug vs. implementation gap.
- Fix the implementation (not the test) unless the test is clearly wrong.
- Re-run the affected tests. Loop until green or until you hit a hard blocker.
- Hard blockers (missing external service, unresolved ambiguous AC) → surface to user and stop.

Do not weaken or delete tests to force them green.

## 6. Report

Produce a concise QA report:

1. **Epic** — name and number resolved.
2. **Unit / integration tests** — files run, pass/fail counts.
3. **E2e tests** — test file(s) run, pass/fail counts, screenshot paths (if `--screenshots` was set).
4. **Overall result** — PASS (all green) or FAIL (with summary of remaining failures).
5. **Action items** — any open issues, deferred fixes, or follow-ups.

Keep the report in chat — do not write it to a file unless the user asks.
