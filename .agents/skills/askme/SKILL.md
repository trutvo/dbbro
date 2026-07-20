---
name: askme
description: Takes a statement, claim, idea, or plan and interactively interrogates it — asking the user clarifying questions round after round, via AskUserQuestion — until it is fully unambiguous, printing a percentage confidence level after every round. Use when the user runs `/askme <statement>` or asks to clarify, pressure-test, refine, or fully pin down a statement/idea before acting on it.
argument-hint: <statement>
allowed-tools: AskUserQuestion
---

# askme — iterative statement clarification

You are running the `askme` skill. Input: `$ARGUMENTS` — a statement, claim, idea, or plan the user wants fully clarified before anything is built or agreed on.

This skill does not write files, specs, or code. It runs a pure clarification loop: read the statement, find what's ambiguous, ask about it, fold the answer in, re-score, repeat — until confidence is high enough or the user can't clarify further.

## 0. Conventions

- **Confidence threshold**: 90%, unless the user's invocation names a different one (e.g. `/askme <statement> --threshold=80`).
- **Max rounds**: 6. If the threshold isn't reached by then, stop anyway and report the remaining gap honestly rather than looping forever.
- **Per round**: ask at most 4 questions (`AskUserQuestion`'s own limit), each with 2–4 concrete options. Every question must include an "Other" implicitly (the tool always offers it) — never force a fit that isn't there.
- Never invent an answer on the user's behalf. If a round's answers leave something still ambiguous, that ambiguity carries into the next round's questions rather than being silently assumed.

## 1. Parse the statement

Take `$ARGUMENTS` as the starting statement, verbatim. Do not rephrase or "improve" it yet — that happens only as clarifications are folded in.

## 2. Score confidence

Score the current statement 0–100 across these axes (lowest wins):

- **Scope** — is it clear what is and isn't covered?
- **Actors** — is it clear who does what, or who is affected?
- **Success criteria** — is it clear what "done" or "true" looks like?
- **Constraints** — are limits, deadlines, non-negotiables named or absent-by-omission?
- **Edge cases** — are the obvious exceptions/failure modes addressed or left open?
- **Terminology** — are key terms used consistently and unambiguously?

Pick the lowest-scoring axis. That's what the next round's questions target — don't ask about an axis that's already clear just to fill a quota.

## 3. Print the confidence line

Before asking anything (including on the very first pass), output a line in the chat:

```
Confidence: ~<NN>% (round <N>) — <one-line reason, naming the lowest-scoring axis and why>
```

This line is always printed — including the round where confidence already clears the threshold on the first pass (round 1, no prior answers) — so the user sees the reasoning, not just a final verdict.

## 4. Decide: stop or ask

- If confidence ≥ the threshold → go to **Step 6 (finish)**.
- If confidence < threshold and round count < max rounds → go to **Step 5 (ask)**.
- If confidence < threshold and round count == max rounds → go to **Step 6 (finish)**, but report it as a stop-by-limit, not a success.

## 5. Ask a round of questions

Use `AskUserQuestion` for 1–4 questions targeting the lowest-scoring axis (and the next-lowest, if there's room within 4). Each question:

- States the specific ambiguity in the statement it's resolving — quote the vague phrase or missing piece directly, so the user knows exactly what's being pinned down.
- Offers 2–4 concrete, mutually exclusive options — not generic "yes/no/other" filler.
- Never pre-selects or recommends an option on the user's behalf — unlike `brainstorm`'s spec-decision cycles, there's no "best practice" default here; the user's own intent is the only source of truth.

After the user answers, fold every answer into the working statement as a direct rewrite (not an appended note) — the statement should read as one coherent thing after each round, the same way `brainstorm` reconciles answers into PRD prose rather than leaving a question-and-answer log inline. Then return to **Step 2** and re-score the *updated* statement fresh — don't reuse the prior round's score.

## 6. Finish

### If confidence ≥ threshold
State: "Confidence ≥ <threshold>% — here's the clarified statement:" followed by the final, fully reconciled statement as clean prose (not a diff, not bullet fragments of each round's answers).

### If stopped by round limit
State plainly that the round limit was reached before full confidence, name the specific axis/axes still weak, and give the best current version of the statement with the remaining ambiguity flagged inline (e.g. "*(still unclear: ...)*") rather than papering over it.

## 7. Hard rules

- Never fabricate an answer to a question you were about to ask the user — if you're tempted to guess, that's a sign it belongs in Step 5, not folded in silently.
- Never ask about something the statement already answers clearly — that wastes a round and the user's patience.
- One round = one `AskUserQuestion` call. Don't split a single round across multiple tool calls.
- Keep the clarified statement itself in plain prose the user actually said/meant — don't dress it up with headers, tables, or spec-speak; this isn't a PRD.
