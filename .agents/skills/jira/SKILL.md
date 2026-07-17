---
name: jira
description: >-
  Interact with Jira exclusively through the `jira` CLI tool. Use when the user
  invokes `/jira`, asks to view, search, create, update, comment on, or
  transition Jira issues, or otherwise needs to read or modify Jira data.
---

# Jira

When the user wants to interact with Jira (including via `/jira`), you **must** use the `jira` CLI tool via the Bash tool. Do not use web fetches, MCP servers, or any other channel for Jira operations.

## Rules

- All Jira reads and writes go through the `jira` CLI.
- If the user gives an issue key (e.g. `ABC-123`), pass it to `jira` directly.
- If a command is unclear, run `jira --help` (or `jira <subcommand> --help`) to discover the right invocation before guessing.
- If `jira` is not installed or not authenticated, stop and tell the user — do not fall back to another method.
