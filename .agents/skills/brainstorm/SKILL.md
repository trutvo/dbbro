---
name: brainstorm
description: Iteratively build an epic PRD, or an epic's technical spec, by asking the user clarifying questions (4 options each, one marked Recommended), dissolving the user's answers into direct requirements/decisions, and repeating until confidence reaches ≥ 90%. Use when the user runs `/brainstorm <epic name or number>` (or `<epic> spec` / `<epic>-spec`) or asks to brainstorm, refine, elicit, or grow a PRD or spec for an epic.
argument-hint: <epic name or number> [spec]
disable-model-invocation: true
allowed-tools: Read Write Edit Bash Glob Grep
---

# brainstorm — iterative PRD / spec builder for an epic

You are running the `brainstorm` skill. Input: `$ARGUMENTS` — the epic name or number to brainstorm, optionally naming the spec.

This skill drives the same iterative loop — ask, reconcile, re-score, repeat until ≥ 90% — over **two possible target documents**:

- the **PRD** (`specs/<num>_<one_liner>.md`), created by this skill itself; or
- the **technical spec** (`specs/<num>_<one_liner>-spec.md`), created by the `write-spec` skill.

Resolve which one you're targeting first (Step 1), then follow the matching branch for reconciliation (Step 3), confidence scoring (Step 4), and question cycles (Step 5). Everything else — the ask/answer/dissolve mechanics, the append-only decision log, the architecture-advisor consultation — is shared.

## 0. Conventions

- **Specs folder**: `specs/` at the repo root (create it if missing).
- **PRD file name**: `specs/<epic-num>_<one_liner>.md`. The `<one_liner>` is `snake_case`, ≤ 6 words, derived from the epic's title.
- **Spec file name**: `specs/<epic-num>_<one_liner>-spec.md` — same stem as the PRD, plus `-spec.md`.
- A **roadmap** at `specs/roadmap.md` may already list the epics. Read it if present and use it to resolve the epic title, scope, dependencies, and briefing alignment.
- Original product briefing lives at `specs/briefing.md` (read if present).

## 1. Resolve the epic and the target document

1. Read `specs/briefing.md` and `specs/roadmap.md` if they exist.
2. Match the epic portion of `$ARGUMENTS` to an epic in the roadmap (by number or fuzzy title). If no match and no roadmap, treat it as the epic title and ask the user once to confirm the file name before creating it.
3. Decide **PRD or spec**:
   - If `$ARGUMENTS` explicitly names the spec (trailing/leading `spec`, `-spec`, `spec-`, a `--spec` flag, or a title that fuzzy-matches an existing `*-spec.md` file more closely than the plain PRD file) → target is the **spec**.
   - Otherwise → target is the **PRD** (the default, unchanged from prior behaviour).
4. If the target is the **spec** and `specs/<num>_<one_liner>-spec.md` does not exist yet: **stop**. Tell the user: "No spec found for epic `<num>`. Run `/write-spec <epic>` first to generate one, then re-run `/brainstorm <epic> spec`." Do not create a spec file yourself — that's `write-spec`'s job.
5. If the target is the **PRD** and it doesn't exist yet, go to Step 2 (create it). If it exists, or the target is the spec (which by Step 4 already exists), go to Step 3 (reconcile).

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

After creating, jump to Cycle 1 (Step 4, PRD branch).

(This step never applies to the spec target — see Step 1.4.)

## 3. Reconcile the target document, then continue

The mechanics are identical for both document types; only the section map differs.

### 3.PRD — PRD section map

1. Read the whole PRD.
2. Find the latest "Clarifying questions — Cycle N" (`§13`) section.
3. For each question, detect the selected option by looking for `[x]` (case-insensitive). If multiple are checked, keep the first and warn the user inline. If none are checked, list the unanswered questions back to the user and stop — do not invent answers.
4. **Reconcile** every selected option into the PRD body as **direct statements** — not as references to the question. Each answer must be expressed in at least one of these places, and never left only as a log entry:
   - **§5 Domain concepts** — when the answer changes an entity, attribute, status, or vocabulary.
   - **§6 User journeys** — when the answer changes what the user sees, types, taps, or what step happens next. Update or add the relevant journey; do not invent a journey just to host a sentence.
   - **§7 Functional requirements** — every answer that defines a system behaviour MUST appear here as a numbered `Fn` item phrased as an imperative requirement ("The system …", "A Member can …"). Group under the existing sub-headings; create a new sub-heading only if the answer doesn't fit any existing one.
   - **§8 Non-functional requirements** — when the answer is a quality attribute (privacy, accessibility, performance, reliability, locale, audit, security, abuse-resistance). Phrase as a numbered `Nn` quality bullet, not a behaviour.
   - **§9 Acceptance criteria** — every answer MUST also produce at least one concrete, testable `ACn` item that a tester could check pass/fail against. Group under the existing AC sub-headings.
5. Reconciliation hygiene:
   - Remove or rewrite any sentence elsewhere in the PRD that now contradicts the decision; the PRD must read as a single coherent spec, not as layers of cycles.
   - Keep FR / NFR / AC numbering stable when you can. If you must renumber, renumber consistently throughout the file (including cross-references).
   - Keep vocabulary consistent with §5 and prior cycles (same status names, role names, entity names).
   - Honour the hard rules in §7 — no tech / architecture decisions sneak in via reconciliation.
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

### 3.SPEC — spec section map

The spec (written by `write-spec`) already carries its architecture decisions as `### D<n>.` blocks inside `§9 Open architecture decisions` — there is no separate numbered question section to dissolve into a log; the decision block itself *is* the question, and answering it means resolving that block in place.

1. Read the whole spec.
2. Scan `§9 Open architecture decisions` for `### D<n>.` blocks with a ticked `[x]` option. If a block has multiple ticks, keep the first and warn the user inline. If a block exists with **no** tick yet, leave it exactly as-is (still open) — do not invent an answer, and do not block the rest of the reconciliation on it.
3. For every `D<n>` block that has exactly one `[x]`:
   - **Reconcile** the chosen option into the document body as a direct statement — not left only inside the decision block:
     - **§3 Architecture** — when the decision changes a module boundary, data flow, integration point, or is itself a "key architecture decision." Add or update the relevant bullet under **Key architecture decisions**.
     - **§4 Data model** — when the decision changes an entity, field, or relationship.
     - **§5 API / interfaces** — when the decision changes a signature, endpoint, or message shape.
     - **§6 Implementation plan (TDD)** — when the decision implies new or changed tasks: add/update the relevant `T<n>` task(s), keeping "closes:" tags accurate.
     - **§7 Non-functional concerns** — when the decision is a quality attribute (performance, security, observability, etc.).
   - **Collapse the resolved `D<n>` block** in `§9` down to a short settled-decision line (no longer four checkbox options): e.g. `**D<n> (resolved):** <decision question> → <chosen option text>, per Cycle <N>.` Keep the architecture-advisor's original rationale as a trailing parenthetical if one was recorded.
   - Append a one-line entry to a **`## 10. Decision log`** section (create it immediately after `§9` if it doesn't exist yet) under a new sub-table for this cycle, in the same shape as the PRD's:
     ```
     ### Cycle <N> — answered
     | #   | Question | Decision |
     | --- | -------- | -------- |
     ```
4. Reconciliation hygiene:
   - Remove or rewrite any sentence elsewhere in the spec that now contradicts the decision.
   - Keep `T<n>` numbering stable when you can; renumber consistently (including "closes:" cross-references) if you must.
   - Keep vocabulary consistent with the PRD the spec is built from — same entity/status/role names.
   - Honour `write-spec`'s hard rules: never invent product requirements; every PRD FR/NFR/AC must stay covered in §2; TDD tests before production code in every §6 task.
5. If `§9` becomes empty of open (unticked) `D<n>` blocks after this pass, remove the `§9 Open architecture decisions` heading entirely (mirroring `write-spec`'s rule that the section only exists when there's something open).
6. The decision log (`§10`) is **append-only across cycles**, exactly like the PRD's.

## 4. Score confidence

**This step is mandatory on every single invocation of this skill, with no exceptions** — including when the question/decision section was already empty on entry, when nothing was answered yet, when the document already reads ≥ 90%, and when nothing changed from the last run. "I already scored this" from a prior turn is never a substitute for re-reading the current file and re-scoring it now. A verbal report to the user without a corresponding `Edit` to the target file does not satisfy this step.

Re-read the target document's current content fresh (do not rely on your memory of a previous pass).

### 4.PRD — PRD axes

Score on a 0–100 scale across these axes, lowest wins:

- Domain concepts unambiguous (entities, relationships, lifecycle).
- All briefing bullets for this epic mapped to FR/AC.
- Personas + journeys cover happy path and the main edge cases (auth outage, abuse, errors).
- Acceptance criteria are concrete and testable.
- Non-functional concerns named (privacy, accessibility, performance, reliability, locale, audit).
- No latent open question that would block implementation.

Persist into the PRD, overwriting the blockquote line directly under the `# Epic …` heading:

```
> **Confidence:** ~<NN>% after Cycle <N> — <one-line summary of the lowest-scoring axis>
```

### 4.SPEC — spec axes

Score on a 0–100 scale across these axes, lowest wins (identical to `write-spec`'s own scoring, so a spec's confidence stays meaningful regardless of which skill last touched it):

- Every PRD FR/NFR/AC still appears in §2 and is closed by at least one §6 task.
- Architecture in §3 is concrete enough to start T1 without further design.
- Each §6 task lists failing tests *before* production code and names real files/functions.
- Any remaining open decisions in §9 are genuinely high-impact (not parking lots) and each has a clear Recommended option.
- No invented requirements; assumptions are explicit.

Persist into the spec, overwriting the blockquote line directly under the `# Epic …` heading:

```
> **Confidence:** ~<NN>% after revision <R> — <one-line summary of the biggest remaining gap>
```

Use "revision" (not "Cycle") to match `write-spec`'s own numbering scheme, and increment `<R>` on every run regardless of which skill is doing the incrementing — the counter belongs to the document, not the tool.

### Shared rules

State the confidence number explicitly to the user (e.g. "Confidence after Cycle 2: ~88%" or "Confidence after revision 3: ~88%").

Overwrite the confidence line on every run, via `Edit`, even when the resulting number and summary are identical to what's already there — the point is that the line reflects a fresh analysis of the current document, not a carried-over string. Never append a second confidence line; there is exactly one per document.

If confidence ≥ 90% → finish (Step 6). Otherwise → run another cycle (Step 5).

## 5. Run a new question cycle

### 5.PRD

Append a new `## 13. Clarifying questions — Cycle <N+1>` section to the PRD with **6–12 questions** targeted at the lowest-scoring axes from Step 4.

### 5.SPEC

Add new `### D<n>.` blocks to `§9 Open architecture decisions` of the spec (creating the section if it was removed) targeted at the lowest-scoring axes from Step 4 — typically gaps in §3 Architecture concreteness or genuinely high-impact choices the PRD doesn't resolve. Number `D<n>` continuing from the highest existing `D` number in the document (including resolved ones), never reusing a number.

Do not use this cycle to relitigate settled product requirements — if the gap is actually a PRD ambiguity, say so to the user and suggest `/brainstorm <epic>` (PRD target) instead of inventing a spec-level decision to paper over it.

### Shared question format

Each question/decision must follow this exact shape:

```
### Q<n>. <short question>
- [ ] Option A — **Recommended** (one-line rationale tied to this product)
- [ ] Option B
- [ ] Option C
- [ ] Option D
```

(For the spec branch, use `### D<n>.` instead of `### Q<n>.`, matching `write-spec`'s existing convention.)

Strict rules:
- **Exactly four options** per question/decision.
- Every option starts with `- [ ]` so the user can flip to `- [x]`.
- **Exactly one option** is marked `**Recommended**`. Never pre-select an option for the user.
- The recommended option is the one that is best for THIS product given the briefing, roadmap, PRD, prior decisions, and any constraints already in the document.
- Options must be concrete and tailored — no generic "best practice / industry standard / other".
- Do not repeat a question/decision that already appears in the decision log unless the user explicitly asked to revisit it.
- Questions probe the gaps that lowered the confidence score, not random topics.

After writing the cycle, tell the user:
- the current confidence score and what dropped it,
- that they should mark one `[x]` per question/decision and re-run `/brainstorm <epic>` (PRD) or `/brainstorm <epic> spec` (spec).

Then stop.

## 6. When confidence ≥ 90% — finish

### 6.PRD
1. Make sure `§13` is empty / removed.
2. Ensure `§11 Open questions` only contains items the team intentionally deferred; everything answered is in the decision log.
3. Tell the user: "Confidence ≥ 90% — PRD for Epic <num> is ready for build." Summarise in 2–3 sentences what changed in this run.

### 6.SPEC
1. Make sure `§9 Open architecture decisions` contains no unticked `D<n>` blocks (remove the section entirely if nothing remains open).
2. Tell the user: "Confidence ≥ 90% — spec for Epic <num> is ready for build." Summarise in 2–3 sentences what changed in this run.

## 7. Hard rules (apply throughout)

- **Never** make architecture or technology decisions in the **PRD** (frameworks, libraries, storage engines, file formats, hosting) — the only exception is when the briefing itself mandates a specific technology. Architecture/technology decisions belong in the **spec**, not the PRD; if a PRD question cycle drifts into one, rewrite it as a product-requirements question instead.
- **Never** select an option on the user's behalf. The user must tick `[x]`.
- **Never** invent product requirements that aren't in the PRD, in either branch. A spec-branch decision must serve an existing PRD FR/NFR/AC — if it doesn't, that's a PRD gap, not a spec decision.

## 8. Architecture-advisor consultation

When a question cycle contains a question/decision that involves a **high-impact architectural or technology choice** (identity/session strategy, data store, caching/rate-limiting, email transport, external APIs, mapping provider, file storage, or changes to cross-cutting access primitives), you **must** spawn the `architecture-advisor` agent before marking any option as `**Recommended**`. This applies to both branches — PRD cycles occasionally surface an architectural question that should be redirected to the spec, and spec cycles are architectural by definition.

How to do it:
1. Identify the architectural questions/decisions in the upcoming cycle.
2. For each one, call the `architecture-advisor` agent with:
   - The decision question text
   - The candidate options you are about to write
   - A brief summary of relevant context (epic name, the specific requirement being served, and — for the spec branch — the relevant PRD FR/NFR/AC)
3. Use the advisor's recommendation to decide which option to mark `**Recommended**`.
4. Append a short note under the recommended option in the form:
   `*(Architecture advisor: <one-sentence reason from the advisor's output)*`

This note is informational only — the user still makes the final call by ticking `[x]`.
- **Never** delete the decision log. It is append-only across cycles.
- **Never** invent briefing content that isn't in `specs/briefing.md` or already in the PRD — if you need a fact that isn't there, turn it into a PRD-branch question.
- Keep vocabulary consistent (same names for entities, statuses, roles across all sections and across the PRD/spec pair).
- Strip backticks from frontmatter values and avoid emojis unless the user added them.
- Prefer `Edit` over full rewrites when updating an existing document.
