# Epic 2 — Record Search

PRD for Record Search. Requirements only — no technical or architectural decisions.

> **Confidence:** ~94% after Cycle 2 — all flows, entities, and match-list mechanics are now fully specified with testable acceptance criteria; no open questions remain.

## 1. Summary

An operator searches for a specific record by first choosing which
table/column combination to search on — drawn from the searchable
table/column pairs declared in the schema configuration (EP-1) — and then
typing the value to look for. dbbro presents this choice as a selection
dialog, takes the search value, and looks up the matching record. This
search dialog is always available, not just at startup: the operator can
reopen it at any point by pressing the `s` key.

## 2. Goals

- Let an operator see every searchable table/column pair the loaded
  configuration declares, in one place, as soon as dbbro starts.
- Let the operator pick exactly one table/column pair using the Up and Down
  keys.
- Let the operator type a search value for the chosen pair and submit it to
  look up the matching record.
- Make the search dialog available on demand, at any time, via the `s` key,
  not only at startup.

## 3. Out of scope

- How the matched record's fields and relations are displayed (Entry Table
  View, EP-3).
- Browsing history / back-and-forth navigation between views (EP-4).
- How search or lookup failures are reported to the operator (Error
  Reporting, EP-5).
- Declaring or validating which tables, columns, and search columns exist
  (Schema Configuration, EP-1) — this epic only consumes that declaration.
- Any free-form or cross-table query capability beyond a single
  table/column/value lookup.

## 4. Personas

- **Operator** — has dbbro running against a configuration set up per EP-1
  and wants to locate a specific record without knowing or writing a query
  language.

## 5. Domain concepts

- **Searchable pair** — a (table, column) combination exposed by the loaded
  configuration (EP-1's search columns). The full list of searchable pairs
  is fixed for the running session.
- **Search selection dialog** — the modal listing all searchable pairs,
  from which the operator picks exactly one using Up/Down.
- **Search value prompt** — the modal, shown after a pair is selected, where
  the operator types the text to search for in that table/column.
- **Search** — the act of submitting a search value for a selected pair,
  which attempts to find a matching record in that table using an exact
  match against the column's stored values.
- **Match outcome** — the result of a search: exactly one match (proceeds to
  Entry Table View, EP-3), multiple matches (a match list is shown for the
  operator to pick from), or no match (an error popup is shown, EP-5).
- **Match list** — the list shown when a search value matches more than one
  record, letting the operator pick which matched record to view. Each row
  shows every configured column of the matched table alongside its value,
  and the list scrolls with Up/Down with no upper limit on match count.

## 6. User journeys

### 6.1 Operator searches at startup
dbbro starts, reads the configuration, and immediately shows the search
selection dialog listing every searchable table/column pair. The operator
moves Up/Down to highlight one pair and presses Return to confirm it. dbbro
then shows the search value prompt for that pair. The operator types a
non-empty value and submits it; dbbro looks up an exact match of that value
in that table's column.

### 6.2 Operator reopens search from anywhere
While viewing something else in dbbro, the operator presses `s`. The search
selection dialog opens showing the same list of searchable pairs, highlight
starting at the first pair. The operator picks a pair, enters a value, and
submits it, triggering a new lookup the same way as 6.1.

### 6.3 Operator cancels out of the search flow
While the search selection dialog is open, the operator presses Escape and
returns to the view they were on before opening it. Alternatively, after
picking a pair, the operator presses Escape while the search value prompt is
open and returns to the search selection dialog without submitting a value.

### 6.4 A search matches more than one record
The operator submits a search value that matches several records. dbbro
shows a match list of those records for the operator to pick from, instead
of proceeding directly to a single record's view. Each row in the match
list shows every configured column of the matched table alongside its
value. The operator moves the highlight with Up and Down, the same keys
used in the search selection dialog, and the list scrolls as needed with
no limit on how many matches it can show. Pressing Return on a highlighted
match proceeds to that record's own table view, the same outcome as if the
search had matched exactly one record. Pressing Escape instead closes the
match list and returns to the view that was on screen before the search
was submitted.

### 6.5 A search matches no record
The operator submits a search value that matches no record. dbbro shows an
error popup (EP-5) naming the table, column, and value that had no match.

### 6.6 Operator reopens the dialog mid-entry
While the search value prompt is open with a partially typed value, the
operator presses `s`. The search selection dialog opens fresh, and the
partially typed value is discarded.

## 7. Functional requirements

### Presenting searchable pairs
1. On startup, the system must derive the full list of searchable
   table/column pairs from the loaded configuration and present them in the
   search selection dialog before any other interaction is required.
2. Each entry in the search selection dialog must identify both the table
   name and the column name of the pair it represents.

### Selecting a pair
3. The operator must be able to move the highlighted selection up and down
   through the list of searchable pairs using the Up and Down keys.
4. The operator must be able to confirm the highlighted pair by pressing
   Return, which then opens the search value prompt for that specific
   table/column.
5. The operator must be able to close the search selection dialog by
   pressing Escape without picking a pair, returning to the view that was
   on screen before the dialog opened.

### Entering and submitting a search value
6. After a pair is selected, the system must prompt the operator to type a
   search value for that pair's column.
7. The system must reject submission of an empty search value; a search
   value must contain at least one character to be submitted.
8. Submitting a non-empty search value must trigger an exact-match lookup
   of that value in the selected table, filtered on the selected column.
9. The operator must be able to press Escape while the search value prompt
   is open to cancel it and return to the search selection dialog, without
   submitting a value.

### Handling match outcomes
10. If exactly one record matches the submitted search value, the system
    must proceed to that record's view.
11. If more than one record matches the submitted search value, the system
    must show a match list of all matching records for the operator to
    pick from.
12. If no record matches the submitted search value, the system must show
    an error popup naming the table, column, and value that had no match.
13. Each entry in the match list must display every configured column of
    the matched table alongside its value.
14. The operator must be able to move the highlighted selection up and
    down through the match list using the Up and Down keys, and the list
    must scroll as needed with no limit on the number of matches shown.
15. The operator must be able to confirm a highlighted match by pressing
    Return, which proceeds to that record's own table view, the same
    outcome as a single-match search.
16. The operator must be able to close the match list by pressing Escape
    without picking a match, returning to the view that was on screen
    before the search was submitted.

### Reopening the dialog
17. The operator must be able to open the search selection dialog at any
    point in the application by pressing the `s` key.
18. Reopening the search selection dialog via `s` must present the same
    full list of searchable pairs as at startup, with the highlight
    starting at the first pair.
19. Reopening the search selection dialog via `s` while a search value
    prompt is mid-entry must discard the in-progress, unsubmitted value.

## 8. Non-functional requirements

1. The search selection dialog must be shown before any other UI is
   usable at startup, so the operator's first action is always a search.
2. Opening the search dialog via `s` must be possible regardless of what
   other view is currently on screen.

## 9. Acceptance criteria

### Presenting searchable pairs
- AC1. Given a loaded configuration with searchable columns declared on one
  or more tables, dbbro's search selection dialog lists exactly those
  table/column pairs, each identified by table name and column name.
- AC2. Given a table with no declared search columns, none of that table's
  columns appear in the search selection dialog.

### Selecting a pair
- AC3. Given the search selection dialog is open, pressing Down moves the
  highlight to the next pair in the list, and pressing Up moves it to the
  previous one.
- AC4. Given a pair is highlighted in the search selection dialog, pressing
  Return opens the search value prompt labeled with that table and column.
- AC5. Given the search selection dialog is open, pressing Escape closes it
  without picking a pair and returns to the previously displayed view.

### Entering and submitting a search value
- AC6. Given the search value prompt is open for a given table/column,
  typing a non-empty value and submitting it initiates an exact-match
  lookup of that value against that table's column.
- AC7. Given the search value prompt is open and empty, submitting is
  rejected and no lookup is triggered.
- AC8. Given the search value prompt is open with a partially typed value,
  pressing Escape returns to the search selection dialog without
  triggering a lookup.

### Handling match outcomes
- AC9. Given a submitted search value matches exactly one record, dbbro
  proceeds to that record's view.
- AC10. Given a submitted search value matches more than one record, dbbro
  shows a match list of all matching records instead of a single record's
  view.
- AC11. Given a submitted search value matches no record, dbbro shows an
  error popup naming the table, column, and value searched.
- AC15. Given the match list is showing multiple matched records, each row
  displays every configured column of the matched table alongside its
  value.
- AC16. Given the match list is open, pressing Down moves the highlight to
  the next match, and pressing Up moves it to the previous one, scrolling
  as needed with no limit on how many matches can be shown.
- AC17. Given a match is highlighted in the match list, pressing Return
  proceeds to that record's own table view.
- AC18. Given the match list is open, pressing Escape closes it without
  picking a match and returns to the view that was on screen before the
  search was submitted.

### Reopening the dialog
- AC12. Given dbbro is showing any view other than the search dialog,
  pressing `s` opens the search selection dialog.
- AC13. Given the search selection dialog was reopened via `s`, it lists
  the same searchable pairs as it did at startup, with the highlight on
  the first pair.
- AC14. Given the search value prompt was mid-entry when `s` was pressed,
  reopening the search selection dialog discards the in-progress value.

## 10. Dependencies and assumptions

- Depends on EP-1 (Schema Configuration) to supply the list of searchable
  table/column pairs; this epic does not itself define what makes a column
  searchable.
- Assumes a matched record's presentation is handled by EP-3 (Entry Table
  View) and a failed lookup's presentation is handled by EP-5 (Error
  Reporting) — this epic covers only the selection and submission flow.

## 11. Open questions

_None — all Cycle 1 questions were resolved; see decision log._

## 12. Decision log

### Cycle 1 — answered
| #   | Question | Decision |
| --- | -------- | -------- |
| Q1  | How should a submitted search value be matched against the column's stored values? | Exact match only |
| Q2  | What happens when a search finds more than one matching record? | Show a list of all matches for the operator to pick from |
| Q3  | What happens when a search finds no matching record? | Show an error popup naming the table/column/value that had no match |
| Q4  | What happens to an in-progress search value prompt when the search dialog is reopened via `s`? | It is discarded |
| Q5  | Does the search selection dialog have a way to cancel/close without picking a pair? | Yes, Escape closes it and returns to the previous view |
| Q6  | Where does the highlight start when the search selection dialog is reopened via `s`? | Always at the first pair in the list |
| Q7  | Can the operator cancel out of the search value prompt back to the search selection dialog? | Yes, via Escape, returning to the search selection dialog |
| Q8  | Is the search value required to be non-empty before it can be submitted? | Yes, an empty value cannot be submitted |
| Q9  | Should the search selection dialog support typing to filter/jump the list? | No — Up/Down only, as described in the briefing |
| Q10 | Does confirming a highlighted pair use the Return key, or a different key? | Return |

### Cycle 2 — answered
| #   | Question | Decision |
| --- | -------- | -------- |
| Q11 | How does the operator move the highlight within the match list? | Up and Down keys, matching the search selection dialog's navigation |
| Q12 | How does the operator confirm a highlighted match in the match list? | Return, matching how a pair is confirmed in the search selection dialog |
| Q13 | What happens once the operator confirms a match from the match list? | dbbro proceeds to that record's own table view, the same outcome as a single-match search |
| Q14 | Can the operator cancel out of the match list without picking a match? | Yes, pressing Escape closes the match list and returns to the view that was on screen before the search was submitted |
| Q15 | What does each entry in the match list display to let the operator distinguish between matches? | Every configured column of the matched table alongside its value, one row per match |
| Q16 | Is there a limit on how many matches the match list can show at once, and if so, how does the operator navigate beyond it? | No limit — the match list shows every matching record and scrolls with Up/Down as needed |
