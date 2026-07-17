# Epic 4 — Browsing History

PRD for Browsing History. Requirements only — no technical or architectural decisions.

> **Confidence:** ~94% after Cycle 1 — all domain concepts, recording/navigation rules, and boundary/key-handling behaviour are unambiguous and mapped to FR/AC; only remaining softness is that "typing in the search value input" as a mode boundary for Left/Right isn't cross-checked against EP-2's own input-focus mechanics (owned by that epic, not this one)

## 1. Summary

As an operator browses table views by searching for records and following
relations, dbbro keeps track of the sequence of table views visited so the
operator can move backward and forward through that sequence the way a web
browser's back/forward navigation works. Only table views are recorded in
this history; opening the search dialog or typing a search value is not
itself a history event.

## 2. Goals

- Let an operator return to a previously viewed table view by pressing the
  Left key, without re-searching or re-selecting a relation.
- Let an operator move forward again to a table view they navigated away
  from via Left, by pressing the Right key.
- Record a new history entry every time a new record's table view is
  displayed, whether reached via search or via following a relation.
- Ensure that opening the search dialog, or entering a search value, does
  not by itself create a history entry — only the resulting table view does.

## 3. Out of scope

- The layout or content of a table view itself (covered by EP-3).
- How a record is found or matched (covered by EP-2).
- How errors are reported or dismissed (covered by EP-5).
- Deciding the in-memory or on-disk representation used to store history
  entries.
- Any history mechanism for anything other than table views (e.g. there is
  no history entry for the search dialog itself).

## 4. Personas

- **Operator** — searches for records and follows relations between table
  views, and wants to retrace or redo steps without repeating a search or
  re-navigating a relation chain.

## 5. Domain concepts

- **History** — an ordered sequence of table views the operator has visited
  during the current running session, together with a notion of the
  operator's current position within that sequence. History does not
  persist across restarts; a new session always starts with empty history.
  History has no fixed size limit and grows for the entire session.
- **History entry** — a single visited table view, added to the history at
  the moment that table view is displayed, whether it was reached by
  submitting a search or by following a relation from another table view.
  A new entry is always added when a table view is displayed, even if it is
  an exact revisit of a record already present elsewhere in the history, and
  even if it is identical to the immediately preceding entry (e.g. a
  relation followed back to the record just come from).
- **Current position** — the history entry corresponding to the table view
  currently on screen; the current table view is itself always a history
  entry, and the current position always points at it.
- **Back navigation** — moving the current position to the entry
  immediately before it in the history, triggered by the Left key, and
  re-displaying that entry's table view.
- **Forward navigation** — moving the current position to the entry
  immediately after it in the history, triggered by the Right key, and
  re-displaying that entry's table view; only available after a back
  navigation has moved the current position away from the most recent
  entry.
- **Forward entries** — history entries positioned after the current
  position, reachable via Right navigation. When a new table view is
  displayed while the current position is not at the most recent entry
  (whether from a search or a followed relation), the new table view
  becomes the entry immediately after the current position, and any
  existing forward entries beyond it are discarded.

## 6. User journeys

### 6.1 Operator navigates back after following relations
The operator searches for a record, then follows one or more relations to
reach further table views. Each of these table views was recorded as a
history entry as it was displayed. The operator presses the Left key and is
returned to the previous table view in that sequence; pressing Left again
continues moving backward, one table view at a time.

### 6.2 Operator navigates forward again
Having pressed Left one or more times, the operator presses the Right key
and is moved forward to the table view they left, one step at a time,
retracing the same path they moved back through.

### 6.3 Operator starts a new path after moving back
The operator has pressed Left to return to an earlier table view, then
performs a new search or follows a different relation from that point. A
new table view is displayed and recorded as a history entry.

### 6.4 Search dialog does not disturb history
The operator opens the search dialog (e.g. by pressing `s`) or types a
search value, then cancels or the search does not (yet) resolve into a
displayed table view. No history entry is created by these actions alone;
the operator's position in the history is unchanged.

### 6.5 Boundary navigation gives no feedback
The operator presses Left while already at the earliest history entry, or
Right while already at the most recent entry. The displayed table view does
not change, and dbbro shows no indicator, popup, or sound to signal that the
boundary was reached; the key press is silently ignored.

### 6.6 Left/Right while typing a search value
The operator has the search dialog open and is typing a value into the
search value input. Pressing Left or Right moves the text cursor within the
input, the same as ordinary text editing, rather than triggering history
navigation. Outside of that input, Left and Right always perform history
navigation.

## 7. Functional requirements

### Recording
1. The system must add a new history entry every time a table view for a
   record is displayed, regardless of whether that table view was reached
   via a search result or via following a relation.
2. Opening the search dialog must not, by itself, create a history entry.
3. Entering or submitting a search value must not, by itself, create a
   history entry; only the table view that results from a successful search
   creates one.

### Back navigation
4. Pressing the Left key must move the current position to the history
   entry immediately preceding it and display that entry's table view.
5. Pressing the Left key while the current position is already at the
   earliest entry in the history must have no effect.

### Forward navigation
6. Pressing the Right key must move the current position to the history
   entry immediately following it and display that entry's table view.
7. Pressing the Right key while the current position is already at the most
   recent entry in the history must have no effect.

### History continuity
8. The Left and Right keys must operate on the same ordered history
   sequence, regardless of whether the operator reached the current table
   view via search or via a followed relation.
9. The currently displayed table view is always itself a history entry, and
   the current position always points at that entry.
10. Every table view display must add a new history entry, even when it is
    an exact revisit of a record already present elsewhere in the history,
    and even when it is identical to the immediately preceding entry (no
    special-casing for revisits or relation cycles).
11. When a new table view is displayed while the current position is not at
    the most recent history entry, whether reached via a new search or via
    following a relation, the new table view must become the entry
    immediately after the current position, and any existing forward
    entries beyond it must be discarded.
12. History must not persist across dbbro restarts; each new running
    session must start with an empty history.
13. The history must not impose a fixed limit on the number of entries it
    can hold within a session.

### Key handling
14. While the operator is typing in the search value input, the Left and
    Right keys must move the text cursor within that input instead of
    triggering history navigation. In every other context, Left and Right
    must perform history navigation.
15. Pressing Left at the earliest history entry, or Right at the most
    recent history entry, must produce no visible feedback beyond leaving
    the displayed table view unchanged — no popup, indicator, or sound.
16. dbbro must not expose any explicit indication of the operator's
    position within history (such as a counter, breadcrumb, or list of
    visited views) beyond the table view currently on screen.

## 8. Non-functional requirements

1. Back and forward navigation must re-display the previously recorded
   table view without requiring the operator to repeat a search or
   relation lookup.
2. Back and forward navigation must be available at any point while a table
   view is on screen, using the same Left/Right key bindings throughout the
   application, except while the operator is typing in the search value
   input, where Left/Right instead move the text cursor.
3. History must be scoped to the current running session only; it must not
   be saved to or restored from any persistent storage across restarts.

## 9. Acceptance criteria

### Recording
- AC1. Given a table view is displayed after a successful search, dbbro
  adds it as a new history entry.
- AC2. Given a table view is displayed after following a relation from
  another table view, dbbro adds it as a new history entry.
- AC3. Given the operator opens the search dialog without submitting a
  search value, no history entry is added.
- AC4. Given the operator submits a search value that does not result in a
  displayed table view, no history entry is added.

### Back navigation
- AC5. Given the operator has visited more than one table view, pressing
  the Left key displays the table view visited immediately before the
  current one.
- AC6. Given the current position is at the earliest table view in the
  history, pressing the Left key leaves the displayed table view unchanged.

### Forward navigation
- AC7. Given the operator has pressed the Left key at least once, pressing
  the Right key displays the table view that was left via that Left key
  press.
- AC8. Given the current position is at the most recent table view in the
  history, pressing the Right key leaves the displayed table view
  unchanged.

### History continuity
- AC9. Given the operator moves back to an earlier table view and then
  performs a new search or follows a different relation, the resulting
  table view is added as a new history entry, and any forward entries that
  existed beyond the current position before this new entry are discarded.
- AC10. Given the operator revisits a record whose table view already
  exists elsewhere in the history (including the immediately preceding
  entry), a new history entry is added rather than reusing the existing
  one.
- AC11. Given the table view currently on screen, it is itself the entry
  the current position points to.

### Boundaries and key handling
- AC12. Given the current position is at the earliest or most recent
  history entry, pressing Left or Right respectively produces no popup,
  indicator, or sound — only the "no effect" behaviour from AC6/AC8.
- AC13. Given the operator is typing in the search value input, pressing
  Left or Right moves the text cursor in that input rather than navigating
  history.
- AC14. Given dbbro is restarted, the new session's history is empty.
- AC15. dbbro does not display any counter, breadcrumb, or list of visited
  table views indicating the operator's position in history.

## 10. Dependencies and assumptions

- Depends on EP-1 (Schema Configuration) for the table/relation structure
  that determines what a table view represents.
- Depends on EP-2 (Record Search) for the search flow that produces the
  table views recorded as history entries.
- Depends on EP-3 (Entry Table View) for the table view display and
  relation-following mechanism that produces history entries.
- Assumes history exists only for the current running session and does not
  need to persist across restarts (no briefing statement addresses this).

## 11. Open questions

_None outstanding — all prior open questions were resolved in Cycle 1 (see
Decision log)._

## 12. Decision log

### Cycle 1 — answered
| #   | Question | Decision |
| --- | -------- | -------- |
| Q1  | What happens to forward entries when the operator navigates back and starts a new path? | Discard all entries ahead of the current position |
| Q2  | Is there a maximum number of table views the history can hold? | No limit — history grows for the entire session |
| Q3  | Is revisiting the same record a new history entry or reuse of the earlier one? | Always add a new history entry, even for an exact revisit |
| Q4  | Does the current table view count as a history entry? | The current table view is itself a history entry, and the current position always points at it |
| Q5  | Should dbbro give feedback when Left/Right has no effect at a boundary? | No feedback — the key press is silently ignored |
| Q6  | Does following a relation back to the immediately preceding entry still add a new history entry? | Yes — every table view display adds a new entry, with no special-casing |
| Q7  | Does history persist across restarts? | History is only ever valid for the current running session |
| Q8  | Where is a new table view inserted when reached via search from a non-latest position? | Becomes the entry immediately after the current position; old forward entries beyond it are discarded |
| Q9  | Should dbbro expose the operator's position within history? | No explicit indication is required beyond the table view itself |
| Q10 | Are Left/Right reserved exclusively for history navigation? | Left/Right perform history navigation except while typing in the search value input, where they move the text cursor |
