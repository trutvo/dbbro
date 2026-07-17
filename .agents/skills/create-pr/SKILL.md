---
name: create-pr
description: "Creates a pull request from the current branch into the project's default branch, using `gh pr create`. Pass --target-branch <branch> to target a different base branch instead of the default. If the current branch already is the target branch, stops and asks the user to create a development branch first rather than opening a PR from the default branch. Use when the user runs `/create-pr` or asks to open/create a pull request for the current branch."
argument-hint: "[--target-branch <branch>]"
disable-model-invocation: true
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(git push:*), Bash(gh pr create:*), Bash(gh repo view:*), Bash(gh pr view:*)
---

# create-pr

You are opening a pull request from the current branch via the `gh` CLI.

Arguments passed by the user: `$ARGUMENTS`

## 1. Resolve the target (base) branch

- `--target-branch <branch>` = an optional flag in `$ARGUMENTS`. If present, use `<branch>` as the base branch.
- If absent, resolve the project's default branch: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`. Fall back to `git remote show origin | grep 'HEAD branch'` if `gh` is unavailable.

## 2. Guard against opening a PR from the target branch itself

1. Get the current branch: `git rev-parse --abbrev-ref HEAD`.
2. If the current branch equals the resolved target branch, **stop**. Tell the user they're on the target branch itself (name it) and ask them to create a development/feature branch first (e.g. `git checkout -b <name>`) before running this skill again. Do not create a branch on their behalf and do not open a PR.

## 3. Verify there's something to open a PR for

1. Run `git status` and `git log <target-branch>..HEAD --oneline`. If there are no commits ahead of the target branch, stop and tell the user — there's nothing to PR.
2. If there are uncommitted changes (`git status` shows modifications), tell the user and ask whether to proceed anyway (a PR only reflects committed work) — do not commit on their behalf; that's the `commit` skill's job.

## 4. Push the branch if needed

- Check if the current branch tracks a remote: `git rev-parse --abbrev-ref --symbolic-full-name @{u}`.
- If it doesn't, push and set upstream: `git push -u origin HEAD`.
- If it does but is ahead of the remote, run `git push`.
- Never force-push.

## 5. Check for an existing PR

Run `gh pr view --json url,state 2>/dev/null` for the current branch. If an open PR already exists targeting the same base branch, report its URL to the user and stop — do not create a duplicate.

## 6. Compose and create the PR

1. Review all commits that will be included: `git log <target-branch>...HEAD` and `git diff <target-branch>...HEAD`.
2. Draft a concise PR title (under ~70 chars, no trailing period) summarizing the change — derive it from the commits, don't just repeat the branch name.
3. Draft a short body with:
   - `## Summary` — 1–3 bullet points of what changed and why.
   - `## Test plan` — bullet checklist of how this was/should be verified, based on what the commits and diff show.
4. Create the PR:

   ```
   gh pr create --base <target-branch> --title "<title>" --body "$(cat <<'EOF'
   <body>

   🤖 Generated with Claude Code
   EOF
   )"
   ```

## 7. Finish

Report the PR URL returned by `gh pr create` to the user.

## Non-goals

- Does not merge, close, or review the PR — creation only.
- Does not commit changes on the user's behalf — the working tree must already reflect what should be in the PR.
- Does not create branches for the user; if the current branch is the target branch, it asks the user to branch off themselves.
- Does not force-push or rewrite history.
