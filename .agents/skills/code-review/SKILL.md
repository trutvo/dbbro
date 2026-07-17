---
name: code-review
description: Reviews the current diff (staged, or unstaged if nothing is staged) for correctness, style, and maintainability issues, adapting to the project's programming language(s) and any local style guide config found in the repo (`.eslintrc*`, `.editorconfig`, `.prettierrc*`, `pyproject.toml`, `.rubocop.yml`, linters, etc). For every issue found, asks the user one at a time to (a) fix it, (b) ignore it, or (c) add it to the exceptions section of `<project-root>/code-review.md`. Use when the user runs `/code-review` or asks to review the current changes / diff. Does not review committed history, whole-repo audits, or PRs on other branches — only the working diff.
argument-hint: "[path or glob to limit the review to]"
disable-model-invocation: true
allowed-tools: Read Bash Glob Grep Edit Write
---

# code-review

You are running the `code-review` skill on the **current diff**, not the whole codebase and not git history.

## 0. Scope

1. Run `git status` and `git diff --cached`. If nothing is staged, review `git diff` (unstaged) instead. If `$ARGUMENTS` gives a path/glob, limit the diff to it (`git diff -- <path>`).
2. If there is no diff at all, tell the user and stop — do not invent issues.
3. Read `<project-root>/code-review.md` if it exists (see §3) — never re-raise an issue that already matches an exception there.

## 1. Detect language and style config

Before reviewing, figure out what rules actually apply to this project instead of guessing from general knowledge:

- Identify the language(s) touched by the diff from file extensions.
- Look for local style/lint config at the project root and nearest ancestor directories, e.g.: `.eslintrc*`, `.prettierrc*`, `biome.json`, `.editorconfig`, `pyproject.toml` (`[tool.black]`, `[tool.ruff]`), `setup.cfg`, `.flake8`, `.rubocop.yml`, `.golangci.yml`, `rustfmt.toml`, `.clippy.toml`, `checkstyle.xml`, `.stylelintrc*`.
- Also check `AGENTS.md` / `CLAUDE.md` for house conventions.
- If a config exists, apply its rules over generic best practice when the two disagree. If no config exists, fall back to established idioms for that language.

## 2. Review the diff

Walk the diff hunk by hunk. For each hunk, look for:

- **Correctness**: logic errors, off-by-one, unhandled edge cases, race conditions, resource leaks.
- **Style**: violations of the detected config/conventions (naming, formatting the linter would flag, import order, etc). Skip purely cosmetic issues an autoformatter would fix silently — flag only what a linter would fail on.
- **Maintainability**: needless complexity, duplicated logic, unclear naming, missing error handling at real boundaries.
- **Security**: injection, secrets, unsafe deserialization, missing auth checks — anything from the OWASP-top-10 family touched by this diff.

Do not flag anything already covered by an exception in `code-review.md` (§3), and do not flag pre-existing code outside the diff's changed lines.

## 3. Exceptions file

Exceptions live at `<project-root>/code-review.md`, a flat file the skill owns (create it if missing, on first use):

```markdown
# Code review exceptions

Issues below were reviewed and explicitly accepted. The code-review skill will not re-raise them.

## <file path>

- L<line or range>: <one-line description of the issue> — accepted <date>, reason: <short reason if the user gave one>
```

Group entries by file. Match future findings against this file by file path + issue description (not exact line number, since lines shift) before reporting them.

## 4. Resolve each issue with the user, one at a time

For every issue that survives §2/§3 filtering, present it (file:line, what's wrong, why) and ask the user to choose:

- **a. Fix it** — make the smallest correct edit yourself via `Edit`, then move to the next issue.
- **b. Ignore it** — skip it, do not modify any file, do not add it to `code-review.md`. It will be raised again on the next review unless the underlying code changes.
- **c. Add exception** — append it to `code-review.md` under §3's format, with today's date and the user's stated reason (or "no reason given").

Use the AskUserQuestion tool for this choice (options: Fix it / Ignore it / Add exception). Do not batch multiple issues into one question — resolve them in order, one at a time, so the user's answer to issue N doesn't get assumed for issue N+1.

## 5. Finish

After all issues are resolved, tell the user:
- how many issues were found, fixed, ignored, and added as exceptions,
- the path to `code-review.md` if it was created or modified.

## Non-goals

- Does not review committed history or generate a report of past commits.
- Does not review other branches, PRs, or the whole repository — diff only.
- Does not run linters/formatters itself or auto-fix formatting; it reasons about the diff by reading the config, it doesn't execute `eslint --fix` or equivalent.
