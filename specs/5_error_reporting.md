# Epic 5 — Error Reporting

PRD for Error Reporting. Requirements only — no technical or architectural
decisions.

> **Confidence:** ~95% after Cycle 1 — remaining gap is minor: no fixed error-message wording examples, but detail level is deliberately unconstrained (see FR3)

## 1. Summary

While an operator is searching for or browsing records, an operation they
triggered can fail — a search that cannot be completed, or a relation lookup
that does not resolve. When that happens, dbbro must clearly tell the
operator what went wrong, let them acknowledge the problem, and return them
to what they were doing without losing their place.

## 2. Goals

- Make every failure of a search or a relation lookup visible to the
  operator as soon as it happens, instead of failing silently or crashing.
- Let the operator dismiss an error notice with a single, consistent action
  and resume exactly where they left off.
- Keep the operator's current view and context intact across an error, so a
  failed operation never discards work in progress (e.g. a pending search
  dialog or the table view they were reading).

## 3. Out of scope

- Retrying the failed operation automatically.
- Logging, persisting, or exporting error details outside of the on-screen
  notice.
- Deciding the wording, layout, or rendering technology of the error notice
  beyond it being a modal dialog dismissible with Return (already specified
  in the briefing).
- Errors originating outside of a search or a relation lookup (e.g.
  configuration loading errors, covered by EP-1).
- Any change to how search (EP-2) or the table view (EP-3, EP-4) behave when
  they succeed.

## 4. Personas

- **Operator** — searches for and browses records through dbbro's UI. Needs
  to know immediately, and in plain terms, when an action they took did not
  work, without dbbro exiting or getting stuck.

## 5. Domain concepts

- **Error notice** — a modal dialog that dbbro shows in place of, or on top
  of, the current view when an operation fails. It describes the problem
  that occurred and stays visible until the operator dismisses it.
- **Failed operation** — an attempt to search for a record (EP-2) or to
  follow a relation to a related record (EP-3) that does not produce a
  result, for reasons outside the operator's control at the point of
  failure (e.g. the lookup could not be completed).
- **Previous view** — whatever the operator was looking at, or the dialog
  they were interacting with, immediately before the failed operation was
  triggered. dbbro returns the operator to this view once the error notice
  is dismissed. For a failed search, this is the search dialog with the
  table/column selection and the typed search value still present, ready to
  edit and resubmit. For a failed relation lookup, this is the table view
  the operator was reading, with the same field still selected.
- **No-match search** — a search that completes without finding a matching
  record. dbbro treats this the same as any other failed search: it shows
  the same error notice, not a distinct empty-result view.
- **Superseded notice** — an error notice that logically still applies but
  is no longer relevant because the operator has since submitted a new
  search. dbbro discards it; only the outcome of the newest attempt is
  shown.

## 6. User journeys

### 6.1 A search fails
The operator opens the search dialog, selects a table/column pair, and
enters a search value. The search cannot be completed, or completes without
matching any record — both are treated as a failed search. dbbro shows an
error notice describing the problem. The operator presses Return, the
notice closes, and the operator is back at the search dialog with the same
table/column selection and the search value they typed still in the input,
able to edit it and try again.

### 6.2 A relation lookup fails
The operator is viewing a record's table view and selects a relation field,
then presses Return to follow it. The related record cannot be looked up.
dbbro shows an error notice describing the problem. The operator presses
Return, the notice closes, and the operator is back on the table view they
were viewing before following the relation, with nothing about that view
changed.

### 6.3 Operator dismisses the notice
While an error notice is on screen, the operator presses Return. The notice
closes immediately and dbbro shows the previous view. No other key closes
the notice while it is open.

### 6.4 Operator retries immediately after an error
The operator dismisses an error notice for a failed search, edits the search
value still shown in the input, and submits again. Whatever notice or
outcome the previous attempt produced no longer matters — only this new
attempt's outcome is shown to the operator.

## 7. Functional requirements

### Triggering
1. The system must show an error notice whenever a search (EP-2) does not
   produce a result because the operation could not be completed, or
   because it completed but matched no record — both count as a failed
   search and are reported the same way.
2. The system must show an error notice whenever following a relation
   (EP-3) does not produce a result because the lookup could not be
   completed.
3. The error notice must describe the problem that occurred in terms the
   operator can act on, limited to stating that the operation failed and
   identifying which operation it was (search vs. relation lookup); it is
   not required to state the underlying cause of the failure.
4. Only search (EP-2) and relation lookup (EP-3) trigger this error-notice
   mechanism; no other operation is in scope for this epic.
5. A single failed operation must always produce exactly one error notice;
   dbbro never shows multiple notices, or a combined notice, for one failed
   attempt.
6. Once the operator submits a new search, any earlier error notice or
   outcome for that same search dialog is superseded and no longer applies;
   only the newest attempt's outcome is shown.

### Presentation
7. The error notice must be shown as a modal dialog, i.e. it takes input
   focus and the view underneath it cannot be interacted with while it is
   shown.
8. The error notice must remain on screen until the operator dismisses it;
   it must not disappear on its own.
9. No search or relation-lookup failure causes dbbro to exit; every such
   failure is recoverable and shown via the dismissible modal notice.

### Dismissal
10. The operator must be able to dismiss an open error notice by pressing
    Return, and Return only; no other key dismisses the notice.
11. Dismissing an error notice must return the operator to the view or
    dialog they were on immediately before the failed operation was
    triggered: the search dialog (with its table/column selection and typed
    search value intact) for a failed search, or the table view (with the
    same field still selected) for a failed relation lookup.
12. Dismissing an error notice must not alter the state of the view it
    returns to (e.g. a table view's selected field, or an in-progress search
    dialog's selection and typed value).
13. A failed operation must not advance the browsing history (EP-4); only
    the view the operator returns to after dismissing the notice counts, and
    it is the same view already present in the history (if any).

## 8. Non-functional requirements

1. An error notice must appear immediately once dbbro determines an
   operation has failed, without requiring further operator action to
   surface it.
2. An error notice's description must be specific enough to distinguish a
   search failure from a relation-lookup failure, and to identify which
   operation failed.
3. Dismissing and re-triggering error notices repeatedly must not degrade
   dbbro's ability to return the operator to their previous view.
4. dbbro must never terminate as a result of a search or relation-lookup
   failure; every such failure is handled through the recoverable modal
   notice.

## 9. Acceptance criteria

### Triggering
- AC1. Given the operator submits a search value that cannot be resolved to
  a result, dbbro shows an error notice instead of an empty or crashed
  view.
- AC2. Given the operator selects a relation field and presses Return, and
  the related record cannot be looked up, dbbro shows an error notice
  instead of an empty or crashed view.
- AC9. Given the operator submits a search value that runs successfully but
  matches no record, dbbro shows the same error notice as any other failed
  search, not a distinct empty-result view.
- AC10. Given a failed search or relation lookup, dbbro shows exactly one
  error notice for that failure, never more than one and never a combined
  notice covering multiple failures.
- AC11. Given an error notice for a failed search is on screen and the
  operator dismisses it, edits the search value, and submits a new search,
  the outcome shown to the operator reflects only the new attempt.

### Presentation
- AC3. Given an error notice is on screen, the operator cannot interact
  with the view underneath it until the notice is dismissed.
- AC4. Given an error notice is on screen, it remains visible until the
  operator presses Return; no timeout or other key closes it.
- AC12. Given any search or relation-lookup failure in scope, dbbro remains
  running and shows the dismissible modal notice rather than exiting.

### Dismissal
- AC5. Given an error notice is on screen and the operator presses Return,
  the notice closes.
- AC6. Given an error notice triggered by a failed search is dismissed, the
  operator is returned to the search dialog with the same table/column
  selection and the previously typed search value still in the input,
  unchanged and editable.
- AC7. Given an error notice triggered by a failed relation lookup is
  dismissed, the operator is returned to the table view they were on
  before following the relation, with the same field still selected and
  nothing else changed.
- AC8. Given a failed operation and its error notice, dismissing the notice
  does not add a new entry to the browsing history.

## 10. Dependencies and assumptions

- Depends on EP-1 (Schema Configuration) for the notion of a valid table,
  column, and relation against which a search or lookup can be attempted
  and can fail.
- Depends on EP-2 (Record Search) as the source of search-failure
  scenarios this epic reports on.
- Assumes EP-3 (Entry Table View) exists to define what "following a
  relation" means and what view the operator returns to after a
  relation-lookup failure; this epic does not define that view itself.
- Assumes dbbro can determine, at the point a search or relation lookup is
  attempted, whether that specific attempt succeeded or failed.

## 11. Open questions

_None outstanding; all prior open questions were resolved in Cycle 1 (see
decision log)._

## 12. Decision log

### Cycle 1 — answered

| #   | Question | Decision |
| --- | -------- | -------- |
| Q1  | Is a zero-match search treated as an error? | Yes, shown via the same error notice as any other failed search |
| Q2  | What happens to an old notice when the operator retries? | The old notice is irrelevant once a new search is submitted; only the newest attempt's outcome matters |
| Q3  | Should any operation besides search/relation lookup trigger this mechanism? | No, only search and relation lookup as stated in the roadmap |
| Q4  | Which view does the operator return to after a failed relation lookup? | The table view of the record they were reading, with the same field still selected |
| Q5  | Can more than one error notice apply to one failed operation? | No, a failed operation always produces exactly one error notice |
| Q6  | Must the notice distinguish why a search or lookup failed? | It only needs to state that the operation failed and which operation it was, not the underlying cause |
| Q7  | Does the typed search value survive dismissal? | Yes, the previously entered search value remains in the input so the operator can edit and resubmit it |
| Q8  | Is any failure severe enough that dbbro should exit? | No, every search or relation-lookup failure is recoverable and shown via the dismissible modal notice |
| Q9  | Can a key other than Return dismiss the notice? | No, Return is the only dismissal key |
