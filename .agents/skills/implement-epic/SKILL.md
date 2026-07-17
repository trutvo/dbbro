---
name: implement-epic
description: Implement an epic end-to-end from its PRD and technical spec. Resolves `specs/<num>_<slug>.md` and `specs/<num>_<slug>-spec.md`, then runs a TDD workflow — analyze → write tests → implement → run tests → fix — until all acceptance criteria are satisfied. Use when the user runs `/implement-epic <epic name or number>` or asks to implement an epic spec.
argument-hint: <epic name or number>
disable-model-invocation: true
allowed-tools: Read Write Edit Bash Glob Grep
---

# implement-epic — execute an epic to green tests

You are running the `implement-epic` skill. Input: `$ARGUMENTS` — the epic name or number.

## 0. Conventions

- **Specs folder**: `specs/` at the repo root.
- **PRD**: `specs/<num>_<slug>.md` (no `-spec` suffix).
- **Tech spec**: `specs/<num>_<slug>-spec.md`.
- Briefing at `specs/briefing.md` and roadmap at `specs/roadmap.md` provide cross-cutting context — read them if they exist.
- Respect `AGENTS.md` / `CLAUDE.md` instructions at the repo root.

## 1. Resolve the epic

1. If `$ARGUMENTS` is a number → glob `specs/<num>_*.md`, pick the PRD (no `-spec`) and its `-spec.md` sibling.
2. If `$ARGUMENTS` is a slug/title → fuzzy match against `specs/*.md`.
3. **If no PRD matches → STOP.** Tell the user: "No PRD found for `<arg>` in `specs/`. Run `/brainstorm <epic>` first."
4. **If no tech spec matches → STOP.** Tell the user: "No tech spec found for `<arg>`. Run `/write-spec <arg>` first."
5. Read both files in full, plus `specs/briefing.md` and `specs/roadmap.md` if present.

## 2. Workflow — TDD loop

Follow these steps in order. Do not skip ahead even if a shortcut looks tempting.

### Step 1 — Analyze the specification
- Enumerate every FR, NFR, and AC from PRD §requirements and §acceptance, and every task from spec §6 (Implementation plan).
- Build an internal task list mapping each AC → planned test(s) → implementation step(s).
- Note any decisions already ticked `[x]` in spec §9 and respect them. If a critical decision is still un-ticked and blocks progress, ask the user once, then continue.

### Step 2 — Build tests from the spec
- Write failing tests **before** implementation, one AC at a time when practical.
- Place tests in the project's conventional location (check `package.json` / existing test dirs).
- Each AC must have at least one assertion that would fail if the requirement is dropped.
- Run the test suite once to confirm the new tests fail for the *right* reason (not import errors).

### Step 3 — Implement the requirements
- Implement just enough code to satisfy the failing tests, following the architecture in spec §3–§5.
- Keep changes minimal and reversible; no speculative abstractions.
- Update or create only files necessary for the ACs in scope.

### Step 4 — Lightweight verify after each task
- After completing each individual task/AC, run only the tests directly related to that task:
  `npx vitest run <path/to/changed-or-new-test-file>`
- Do **not** run the full suite or e2e tests here — that is deferred to the final QA gate (§3).
- Capture failures verbatim and fix before moving to the next task.

### Step 5 — Fix until the task's tests are green
- For each failure in the task-scoped run, diagnose root cause and fix.
- Re-run after each fix. Loop steps 4–5 until the task's tests pass.
- Do not delete or weaken tests to make them pass.

## 3. Stop conditions

- All per-task tests are green AND every AC has at least one passing test → proceed to §4.
- If you reach a hard blocker (missing external dependency, ambiguous AC that the user must resolve), stop and surface it instead of guessing.

## 4. Full QA gate — invoke verify-epic

Once all tasks are implemented and their lightweight tests are green, run the full QA suite by invoking the `verify-epic` skill for this epic:

```
/verify-epic <epic name or number>
```

- Pass `--screenshots` only if the user originally requested it.
- Do not proceed to §5 until `verify-epic` reports an overall **PASS**.
- If `verify-epic` surfaces failures, fix them and re-run `verify-epic` until green.

## 5. Final report

Produce a concise report with:

1. **Summary** — one paragraph: what was implemented, test counts (added / passing).
2. **Acceptance criteria coverage table**:

   | AC ID | Status                   | Test(s)              | Notes |
   | ----- | ------------------------ | -------------------- | ----- |
   | AC-1  | done / partly / not done | `path/to/test::name` | …     |

   - **done** — implemented and covered by passing test(s).
   - **partly** — implemented but with caveats (missing edge case, deferred sub-requirement) — explain.
   - **not done** — explicitly out of scope or blocked — explain why.
3. **Deviations from the spec** — anything you changed vs. spec §3–§6, with reasoning.
4. **Follow-ups** — TODOs, known issues, or recommended next epics.

Keep the report in the chat — do not write it to a file unless the user asks.
