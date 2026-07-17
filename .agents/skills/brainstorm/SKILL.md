---
name: brainstorm
description: Iteratively build an epic PRD by asking the user clarifying questions (4 options each, one marked Recommended), dissolving the user's answers into direct requirements / user journeys / acceptance criteria, and repeating until confidence reaches ≥ 90%. Use when the user runs `/brainstorm <epic name or number>` or asks to brainstorm, refine, elicit, or grow a PRD for an epic.
argument-hint: <epic name or number>
disable-model-invocation: true
allowed-tools: Read Write Edit Bash Glob Grep
---

# brainstorm — iterative PRD builder for an epic

You are running the `brainstorm` skill. Input: `$ARGUMENTS` — the epic name or number to brainstorm.

## 0. Conventions

- **Specs folder**: `specs/` at the repo root (create it if missing).
- **PRD file name**: `specs/<epic-num>_<one_liner>.md`. The `<one_liner>` is `snake_case`, ≤ 6 words, derived from the epic's title.
- If `$ARGUMENTS` is just a number, look for `specs/<num>_*.md`; if just a slug, look for any matching file; if no match exists, create a new PRD.
- A **roadmap** at `specs/roadmap.md` may already list the epics. Read it if present and use it to resolve the epic title, scope, dependencies, and briefing alignment.
- Original product briefing lives at `specs/briefing.md` (read if present).

## 1. Resolve the epic

1. Read `specs/briefing.md` and `specs/roadmap.md` if they exist.
2. Match `$ARGUMENTS` to an epic in the roadmap (by number or fuzzy title).
3. If no match and no roadmap, treat `$ARGUMENTS` as the epic title and ask the user once to confirm the file name before creating it.

## 2. If the PRD does not yet exist — create it

Create `specs/<num>_<one_liner>.md` with this skeleton, filling each section from the briefing + roadmap:

```
# Epic <num> — <Title>

PRD for <epic title>. Requirements only — no technical or architectural decisions.

> **Confidence:** _initial draft_ — Cycle 0, ~0% (to be re-scored at the end of every cycle)

## 1. Summary
## 2. Goals
## 3. Out of scope
## 4. Personas
## 5. Domain concepts
## 6. User journeys
## 7. Functional requirements
## 8. Non-functional requirements
## 9. Acceptance criteria
## 10. Dependencies and assumptions
## 11. Open questions
## 12. Decision log
## 13. Clarifying questions — Cycle <N>
```

Rules for the initial draft:
- No technology choices, no architecture, no library names, no file formats unless the briefing itself mandates them.
- Cover every briefing bullet that maps to this epic.
- Personas, journeys, FRs, NFRs, and ACs are all required.
- Section 11 "Open questions" lists known gaps in prose; section 13 turns them into a question round.

After creating, jump to Cycle 1 (Step 4).

## 3. If the PRD already exists — reconcile then continue

1. Read the whole PRD.
2. Find the latest "Clarifying questions — Cycle N" section.
3. For each question, detect the selected option by looking for `[x]` (case-insensitive). If multiple are checked, keep the first and warn the user inline. If none are checked, list the unanswered questions back to the user and stop — do not invent answers.
4. **Reconcile** every selected option into the PRD body as **direct statements** — not as references to the question. Each answer must be expressed in at least one of these places, and never left only as a log entry:
   - **§5 Domain concepts** — when the answer changes an entity, attribute, status, or vocabulary.
   - **§6 User journeys** — when the answer changes what the user sees, types, taps, or what step happens next. Update or add the relevant journey; do not invent a journey just to host a sentence.
   - **§7 Functional requirements** — every answer that defines a system behaviour MUST appear here as a numbered `Fn` item phrased as an imperative requirement ("The system …", "A Member can …"). Group under the existing sub-headings (Domain, Identity &amp; access, Anti-abuse, Cross-cutting, …); create a new sub-heading only if the answer doesn't fit any existing one.
   - **§8 Non-functional requirements** — when the answer is a quality attribute (privacy, accessibility, performance, reliability, locale, audit, security, abuse-resistance). Phrase as a numbered `Nn` quality bullet, not a behaviour.
   - **§9 Acceptance criteria** — every answer MUST also produce at least one concrete, testable `ACn` item that a tester could check pass/fail against. Group under the existing AC sub-headings.
5. Reconciliation hygiene:
   - Remove or rewrite any sentence elsewhere in the PRD that now contradicts the decision; the PRD must read as a single coherent spec, not as layers of cycles.
   - Keep FR / NFR / AC numbering stable when you can. If you must renumber, renumber consistently throughout the file (including cross-references inside the PRD).
   - Keep vocabulary consistent with §5 and prior cycles (same status names, role names, entity names).
   - Honour the hard rules in §7 of this skill — no tech / architecture decisions sneak in via reconciliation.
6. **Dissolve the answered questions** out of §13:
   - For every question that received an `[x]`, append a one-line entry to **§12 Decision log** under a new sub-table for this cycle:
     ```
     ### Cycle <N> — answered
     | #   | Question | Decision |
     | --- | -------- | -------- |
     ```
   - Use a short paraphrase for "Question" and the picked option's text (without the "**Recommended**" marker) for "Decision".
   - Then **delete the entire `§13 Clarifying questions — Cycle <N>` block** from the PRD. After this skill runs, the PRD must contain no `[ ]` / `[x]` checkboxes and no question prose — only the decision log preserves the history.
7. The decision log is **append-only across cycles**. Never edit or remove an earlier "Cycle N — answered" sub-table; only add new ones.

## 4. Score confidence

Score on a 0–100 scale across these axes, lowest wins:

- Domain concepts unambiguous (entities, relationships, lifecycle).
- All briefing bullets for this epic mapped to FR/AC.
- Personas + journeys cover happy path and the main edge cases (auth outage, abuse, errors).
- Acceptance criteria are concrete and testable.
- Non-functional concerns named (privacy, accessibility, performance, reliability, locale, audit).
- No latent open question that would block implementation.

State the confidence number explicitly to the user (e.g. "Confidence after Cycle 2: ~88%").

**Persist the confidence into the PRD.** Update the blockquote line directly under the `# Epic …` heading to read:

```
> **Confidence:** ~<NN>% after Cycle <N> — <one-line summary of the lowest-scoring axis>
```

Every cycle MUST overwrite this line so it always reflects the latest score. Never append a second confidence line; there is exactly one per document.

If confidence ≥ 90% → finish (Step 6). Otherwise → run another cycle (Step 5).

## 5. Run a new question cycle

Append a new `## 13. Clarifying questions — Cycle <N+1>` section to the PRD with **6–12 questions** targeted at the lowest-scoring axes from Step 4.

Each question must follow this exact shape:

```
### Q<n>. <short question>
- [ ] Option A — **Recommended** (one-line rationale tied to this product)
- [ ] Option B
- [ ] Option C
- [ ] Option D
```

Strict rules:
- **Exactly four options** per question.
- Every option starts with `- [ ]` so the user can flip to `- [x]`.
- **Exactly one option** is marked `**Recommended**`. Never pre-select an option for the user.
- The recommended option is the one that is best for THIS product given the briefing, roadmap, prior decisions, and any constraints already in the PRD.
- Options must be concrete and tailored — no generic "best practice / industry standard / other".
- Do not repeat a question that already appears in the decision log unless the user explicitly asked to revisit it.
- Questions probe the gaps that lowered the confidence score, not random topics.

After writing the cycle, tell the user:
- the current confidence score and what dropped it,
- that they should mark one `[x]` per question and re-run `/brainstorm <epic>`.

Then stop.

## 6. When confidence ≥ 90% — finish

1. Make sure `§13` is empty / removed.
2. Ensure `§11 Open questions` only contains items the team intentionally deferred; everything answered is in the decision log.
3. Tell the user: "Confidence ≥ 90% — PRD for Epic <num> is ready for build." Summarise in 2–3 sentences what changed in this run.

## 7. Hard rules (apply throughout)

- **Never** make architecture or technology decisions in the PRD (frameworks, libraries, storage engines, file formats, hosting). The only exception is when the briefing itself mandates a specific technology (e.g. "use OpenStreetMap").
- **Never** select an option on the user's behalf. The user must tick `[x]`.

## 8. Architecture-advisor consultation

When a question cycle contains a question that involves a **high-impact architectural or technology choice** (identity/session strategy, data store, caching/rate-limiting, email transport, external APIs, mapping provider, file storage, or changes to cross-cutting access primitives), you **must** spawn the `architecture-advisor` agent before marking any option as `**Recommended**`.

How to do it:
1. Identify the architectural questions in the upcoming cycle.
2. For each such question, call the `architecture-advisor` agent with:
   - The decision question text
   - The candidate options you are about to write
   - A brief summary of relevant PRD context (epic name, the specific requirement being served)
3. Use the advisor's recommendation to decide which option to mark `**Recommended**`.
4. Append a short note under the recommended option in the form:
   `*(Architecture advisor: <one-sentence reason from the advisor's output)*`

This note is informational only — the user still makes the final call by ticking `[x]`.
- **Never** delete the decision log. It is append-only across cycles.
- **Never** invent briefing content that isn't in `specs/briefing.md` or already in the PRD — if you need a fact that isn't there, turn it into a question.
- Keep the PRD's vocabulary consistent (same names for entities, statuses, roles across all sections).
- Strip backticks from frontmatter values and avoid emojis unless the user added them.
- Edits to existing PRDs prefer the `Edit` tool over full rewrites whenever feasible.
