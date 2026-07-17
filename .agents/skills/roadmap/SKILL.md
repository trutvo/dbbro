---
name: roadmap
description: "Reads specs/briefing.md (or a Jira ticket's description, e.g. /roadmap MYTSDOWN-1234) and produces specs/roadmap.md — a requirement-only epic breakdown (max N epics, default 5) with resolved dependencies and parallel implementation opportunities identified. Accepts an optional --max-epics parameter to override the epic limit (e.g. /roadmap --max-epics=3)."
---

# roadmap

You read `specs/briefing.md` and produce `specs/roadmap.md` — a delivery roadmap
that breaks the goal into at most `$MAX_EPICS` epics, resolves their dependencies,
and identifies which epics can run in parallel.

## Argument parsing

`$ARGUMENTS` may contain an optional `--max-epics=<N>` (or `--max-epics <N>`)
parameter that sets the maximum number of epics, and an optional Jira ticket ID
(a token matching `[A-Z][A-Z0-9]*-[0-9]+`, e.g. `MYTSDOWN-1234`) that overrides
the briefing source.

- If `--max-epics` is given with a positive integer, use it as `$MAX_EPICS`.
- If `--max-epics` is absent, use `5` as `$MAX_EPICS`.
- If `--max-epics` is present but not a positive integer, stop immediately and
  report: "Usage: /roadmap [--max-epics=N] [TICKET-ID]  — e.g. /roadmap --max-epics=3  (default: 5)"
- If a Jira ticket ID is present, use it as `$TICKET_ID` and read the briefing
  from that ticket instead of `specs/briefing.md` (see **Briefing source**).

## Briefing source

- If `$TICKET_ID` is set:
  1. Fetch the ticket via the `jira` CLI, e.g. `jira issue view $TICKET_ID`.
     Interact with Jira exclusively through the `jira` CLI tool — never guess
     at a REST endpoint or URL.
  2. If the ticket cannot be found (non-zero exit code, "not found", permission
     error, etc.), stop immediately and report the exact error from the `jira`
     CLI. Do not fall back to `specs/briefing.md` and do not write
     `specs/roadmap.md`.
  3. Otherwise, use the ticket's description field as the briefing content in
     place of `specs/briefing.md` for the rest of this skill (goal, functional
     requirements, non-functional requirements).
- If `$TICKET_ID` is not set, read `specs/briefing.md` as described in Startup.

## What this skill does NOT do

- Make technology or architecture decisions (no crate names, data structures,
  protocols, file formats, or implementation strategies)
- Prescribe how something is built — only what behaviour must exist when it is done
- Add epics for work not traceable to a requirement in the briefing

## Startup

1. Read the briefing (see **Briefing source**) to extract the stated goal,
   functional requirements, and any non-functional requirements (e.g. timing,
   frequency, safety).
2. Check whether `specs/roadmap.md` already exists; if it does, read it before
   overwriting so you can preserve any content that is still accurate.
3. Scan `specs/EP-*.md` files (if any) to understand epics already defined, and
   avoid duplicating work that is already captured.

## Analysis

Before writing anything, reason through:

1. **Requirements inventory** — list every distinct functional and non-functional
   requirement from the briefing. Each requirement must end up inside at least one
   epic's acceptance criteria.
2. **Epic candidates** — group related requirements into candidate epics. Aim for
   the fewest epics that keep each one independently deliverable and testable.
   Hard limit: `$MAX_EPICS` epics.
3. **Dependency resolution** — for each epic pair, determine whether one must be
   complete before the other can begin. An epic A depends on epic B only when A's
   acceptance criteria cannot be verified without the behaviour that B delivers.
   Express transitive dependencies explicitly (if C depends on B and B depends on A,
   list A as a dependency of C even if C never mentions A directly).
4. **Parallelism** — mark any epics that have no dependency between them as
   parallelisable. State this explicitly in the roadmap so implementors know which
   streams of work can proceed simultaneously.

## Output format

Write `specs/roadmap.md` using this structure (no HTML tags, aligned table columns):

```
# Roadmap: <goal title from briefing>

<one or two sentences restating the goal and the target end-state>

---

## Dependency graph

| Epic | Depends on | Can start in parallel with |
| ---- | ---------- | -------------------------- |
| EP-1 | —          | EP-2                       |
| EP-2 | —          | EP-1                       |
| EP-3 | EP-1, EP-2 | —                          |

---

## EP-1 — <Short title>

<Two to four sentences describing what behaviour must exist when this epic is
done. Write from the perspective of a user or operator observing the system —
not from an implementor's perspective.>

**Acceptance criteria**

- <Observable behaviour 1>
- <Observable behaviour 2>
- ...

---

## EP-2 — <Short title>

...
```

Rules for each epic section:

- The title must name the capability, not a technical component
  (e.g. "Tick Counter" not "Atomic u64 on Engine Struct").
- The description must be written as user-observable behaviour, not as
  implementation steps.
- Acceptance criteria must be testable from the outside: "given X, the system
  does Y" — no references to internal structures, crates, or source files.
- Non-functional requirements (e.g. "must not introduce delay to the timing loop",
  "client controls polling frequency") belong as acceptance criteria on the epic
  that delivers the feature they constrain.

## Quality checklist

Before writing the file, verify:

- [ ] Every requirement from the briefing is covered by at least one acceptance criterion.
- [ ] No epic has more than one primary responsibility.
- [ ] No acceptance criterion mentions a technology, crate, data structure, or file.
- [ ] The dependency graph is consistent with the epic descriptions.
- [ ] Parallel epics genuinely have no ordering dependency between them.
- [ ] The total epic count is `$MAX_EPICS` or fewer.
- [ ] No HTML tags anywhere in the file.
- [ ] All table columns are aligned (pipe characters line up vertically).

## Writing the file

Once the analysis passes the quality checklist, write `specs/roadmap.md`.
Report:
- How many epics were created and why that number was chosen.
- Which epics can run in parallel and why.
- Any requirement from the briefing that was ambiguous and how you resolved it.

