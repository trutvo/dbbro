---
name: confluence
description: >-
  Interact with Confluence exclusively through the `confluence` CLI tool. Use
  when the user invokes `/confluence`, asks to view, search, create, update,
  comment on, or otherwise needs to read or modify Confluence pages.
---

# Confluence

When the user wants to interact with Confluence (including via `/confluence`), you **must** use the `confluence` CLI tool via the Bash tool. Do not use web fetches, MCP servers, or any other channel for Confluence operations.

## Rules

- All Confluence reads and writes go through the `confluence` CLI.
- If the user gives a page ID or space key, pass it to `confluence` directly.
- If a command is unclear, run `confluence --help` (or `confluence <subcommand> --help`) to discover the right invocation before guessing.
- If `confluence` is not installed or not authenticated, stop and tell the user — do not fall back to another method.
