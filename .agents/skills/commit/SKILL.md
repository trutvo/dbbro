---
name: commit
description: "Creates a git commit whose message follows the schema '[{ticket_id}] {user_message} {agent_message}'. Takes a ticket id and an optional user message as arguments (e.g. /commit MYTSDOWN-2577 fix flaky retry). Pass --push anywhere in the arguments to push the commit afterwards (e.g. /commit MYTSDOWN-2577 fix flaky retry --push)."
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(git rev-parse:*), Bash(git branch:*)
---

# commit

Create a git commit whose message follows this exact schema:

```
[{ticket_id}] {user_message} {agent_message}
```

Arguments passed by the user: `$ARGUMENTS`

Parsing rules:
- `--push` = an optional flag that may appear anywhere in `$ARGUMENTS`. If present, strip it out before applying the rules below, and push the commit after it's created (see step 7). If absent, do not push.
- `{ticket_id}` = the first whitespace-delimited token of the remaining arguments (e.g. `MYTSDOWN-2577`, `PL-3873`). Wrap it in square brackets.
- `{user_message}` = everything after the first token. May be empty — if empty, omit it (and the surrounding space) so the message becomes `[{ticket_id}] {agent_message}`.
- `{agent_message}` = a concise, single-sentence description of the change that you derive from the diff. Focus on the *why*, not a mechanical restatement of the diff.
- If the remaining arguments are empty or the first token does not look like a ticket id (uppercase letters + dash + digits), stop and ask the user for the ticket id instead of guessing.

Steps:
1. Run `git status` and `git diff --cached`. If nothing is staged, also run `git diff` to see unstaged changes; stage only the files relevant to this commit by name (never `git add -A` / `git add .`).
2. Screen every candidate file for secrets and generated artifacts before staging or committing:
   - **Secrets**: refuse to commit files whose name or content suggests credentials — e.g. `.env`, `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `*.keystore`, `credentials*`, `secrets*`, `*.tfvars`, service-account JSON, files containing high-entropy strings or assignments like `AWS_SECRET_ACCESS_KEY=`, `API_KEY=`, `password=`, `token=`, private key headers (`-----BEGIN ... PRIVATE KEY-----`), JWTs, or similar. Inspect `git diff` for inline secrets too, not just filenames.
   - **Generated files**: refuse to commit build output, dependency directories, lockfile noise, or other machine-generated artifacts — e.g. `node_modules/`, `dist/`, `build/`, `out/`, `target/`, `.next/`, `.nuxt/`, `coverage/`, `__pycache__/`, `*.pyc`, `*.class`, `*.o`, `*.so`, `*.exe`, `.DS_Store`, IDE folders (`.idea/`, `.vscode/` unless tracked), minified bundles, and anything matched by the repo's `.gitignore`. Check `git check-ignore` if unsure.
   - If you detect either, drop the file from the commit and tell the user which file and why. If the file is already tracked but looks generated/secret, stop and ask before proceeding. Suggest adding it to `.gitignore` (and rotating the secret) when relevant.
3. Run `git log --oneline -10` to match the repository's commit-message style.
4. Compose the commit message per the schema above. Keep the full subject line short (under ~72 chars where possible). If extra detail is genuinely useful, put it in the body — never expand the subject.
5. Create the commit using a HEREDOC and append the standard trailer:

   ```
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
6. Run `git status` afterwards to verify the commit landed.
7. If `--push` was passed, push the current branch: check whether it tracks a remote (`git rev-parse --abbrev-ref --symbolic-full-name @{u}`); if it does, run `git push`, otherwise run `git push -u origin HEAD`. Never force-push. If the push fails (e.g. diverged from remote), stop and report the error to the user instead of resolving it yourself. If `--push` was not passed, do not push.

Constraints:
- Do not push unless `--push` was passed.
- Never force-push, even if `--push` was passed.
- Do not amend an existing commit; always create a new one.
- Do not pass `--no-verify` or otherwise skip hooks.
- If a pre-commit hook fails, fix the underlying issue and create a new commit (do not amend).
- Never commit secrets or generated files, even if the user explicitly asks — warn instead and wait for confirmation that overrides the safeguard.
