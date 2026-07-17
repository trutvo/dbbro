---
name: write-spec
description: Generate a detailed technical specification from an existing epic PRD. Reads `specs/<num>_<slug>.md`, covers every FR/NFR/AC, plans implementation tasks in TDD order, highlights key architecture decisions, and appends high-impact open decisions as `[ ]` options for the user to tick. Use when the user runs `/write-spec <epic name or number>` or asks to turn a PRD into a tech spec. Stops if no PRD exists.
argument-hint: <epic name or number>
disable-model-invocation: true
allowed-tools: Read Write Edit Bash Glob Grep
---

# write-spec — PRD → technical specification

You are running the `write-spec` skill. Input: `$ARGUMENTS` — the epic name or number.

## 0. Conventions

- **Specs folder**: `specs/` at the repo root.
- **PRD file**: `specs/<num>_<one_liner>.md` (created by the `brainstorm` skill).
- **Output spec file**: `specs/<num>_<one_liner>-spec.md` — same stem as the PRD, plus `-spec.md`.
- Briefing at `specs/briefing.md` and roadmap at `specs/roadmap.md` provide cross-cutting context — read them if they exist.

## 1. Resolve the PRD

1. If `$ARGUMENTS` is a number → glob `specs/<num>_*.md` (must exclude `*-spec.md`).
2. If `$ARGUMENTS` is a slug or title → fuzzy match against `specs/*.md` (excluding `*-spec.md`).
3. **If no PRD matches → STOP.** Tell the user: "No PRD found for `<arg>` in `specs/`. Run `/brainstorm <epic>` first." Do not create any files.
4. Read the full PRD, plus `specs/briefing.md` and `specs/roadmap.md` if present.

## 2. Prepare the output file

- Target path: `specs/<num>_<one_liner>-spec.md`.
- If it already exists, read it and update via `Edit` rather than overwriting. Preserve any `[x]` ticks the user already made in §9.

## 3. Spec skeleton

Write the spec with these sections:

```
# Epic <num> — <Title> — Technical Specification

Tech spec for `<prd-file>`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~<NN>% after revision <R> — <one-line summary of the biggest remaining gap>

## 1. Overview
## 2. Requirements coverage
## 3. Architecture
## 4. Data model
## 5. API / interfaces
## 6. Implementation plan (TDD)
## 7. Non-functional concerns
## 8. Risks & mitigations
## 9. Open architecture decisions
```

### §1 Overview
Two or three sentences: what is being built, scope boundary, link to the PRD by relative path.

### §2 Requirements coverage
Exhaustive table mapping **every** PRD item to the section(s) of this spec that satisfy it. Build the table by walking the PRD's §7 (FR), §8 (NFR), and §9 (AC) in order — no item may be missing.

```
| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| F1      | …       | §3, §6 T2  |
| AC3     | …       | §6 T4      |
```

### §3 Architecture
Describe components, data flow, integration points, key modules. Inline, call out **Key architecture decisions** with a short rationale for each — these are the decisions you are making *now* (not deferring to §9).

### §4 Data model
Entities, fields, relationships, lifecycle/state transitions. Omit if not relevant for this epic.

### §5 API / interfaces
Endpoints, function signatures, events, message shapes — whatever the epic exposes to the rest of the system.

### §6 Implementation plan (TDD)
Ordered list of tasks `T1, T2, …`. **Every task is written TDD-first.** Each task block:

```
### T<n>. <task title>            (closes: F1, AC3)
- Failing tests to write first:
  - <unit / integration / e2e test name and intent>
- Production code to make them pass:
  - <files / functions / modules>
- Refactor step:
  - <what to clean up once green>
```

The "closes" tag must reference PRD items from §2 — together, all tasks must close every row in the coverage table.

### §7 Non-functional concerns
Performance, security, privacy, accessibility, observability, locale, audit — whichever NFRs the PRD raised, plus any cross-cutting concerns the implementation introduces.

### §8 Risks & mitigations
Short bullet list. One line per risk, one line per mitigation.

### §9 Open architecture decisions
Include this section **only if there are high-impact architecture or technology decisions you do not want to make unilaterally**. Otherwise omit it entirely.

Format — mirrors the `brainstorm` skill so the user can tick `[x]`:

```
### D<n>. <decision question>
- [ ] Option A — **Recommended** (one-line rationale tied to this product)
- [ ] Option B
- [ ] Option C
- [ ] Option D
```

Strict rules:
- Exactly four options per decision.
- Exactly one option marked `**Recommended**`.
- Every option starts with `- [ ]` so the user can flip to `- [x]`.
- Options are concrete and tailored — no generic "best practice / other".
- Never tick an option for the user.

### Confidence score

After writing or updating the spec, score your confidence on a 0–100 scale across:

- Every PRD FR/NFR/AC appears in §2 and is closed by at least one §6 task.
- Architecture in §3 is concrete enough to start T1 without further design.
- Each §6 task lists failing tests *before* production code and names real files/functions.
- Open decisions in §9 are genuinely high-impact (not parking lots) and each has a clear Recommended option.
- No invented requirements; assumptions are explicit.

Lowest axis wins. Overwrite the blockquote line directly under the `# Epic …` heading to read:

```
> **Confidence:** ~<NN>% after revision <R> — <one-line summary of the biggest remaining gap>
```

Increment `<R>` on every run. There is exactly one confidence line per spec — never append a second.

## 4. Hard rules

- **Never** invent product requirements that aren't in the PRD. If you need one, raise it in §9 or note it as an explicit assumption in §1.

## 4a. Architecture-advisor consultation

Before marking any `§9 Open architecture decisions` option as `**Recommended**`, you **must** spawn the `architecture-advisor` agent for every decision in that section.

How to do it:
1. For each `D<n>` decision you are about to write, call the `architecture-advisor` agent with:
   - The decision question
   - The candidate options
   - The relevant PRD requirement(s) being served
2. Use the advisor's recommendation to decide which option to mark `**Recommended**`.
3. Append the advisor's one-sentence reason as a note directly under the recommended option:
   `*(Architecture advisor: <reason>)*`

This note must appear in the spec so readers understand why the option was recommended. The user still makes the final call by ticking `[x]`.
- **Every** PRD FR / NFR / AC must appear in the §2 coverage table and be closed by at least one §6 task.
- TDD is mandatory in §6: failing tests are listed *before* production code in every task.
- Stay consistent with PRD vocabulary — same entity, status, and role names.
- Honour `AGENTS.md`: this project's Next.js has breaking changes — consult `node_modules/next/dist/docs/` before recommending Next.js APIs or conventions.
- Prefer `Edit` over full rewrites when updating an existing spec; preserve the user's `[x]` ticks in §9.
- Strip backticks from frontmatter values and avoid emojis unless the user added them.

## 5. Finish

Tell the user:
- the path of the spec file you wrote or updated,
- a 2–3 sentence summary of what it covers,
- if §9 exists, the number of open decisions and a prompt to tick `[x]` on the options they want.
