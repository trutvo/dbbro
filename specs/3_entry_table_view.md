# Epic 3 — Entry Table View

PRD for Entry Table View. Requirements only — no technical or architectural decisions.

> **Confidence:** ~93% after Cycle 1 — all prior edge-case gaps are resolved and testable; the only residual softness is that the new breadcrumb feature (FR5/AC5) overlaps conceptually with EP-4's browsing history and its exact reconciliation is left to EP-4's implementation rather than fully specified here.

## 1. Summary

Once a search (EP-2) finds a matching record, the operator needs to actually
see it. dbbro lays out every configured column of the matched record's table
as a two-column table (column name and value), makes any relation columns
visibly distinct and navigable, and lets the operator jump into a related
record by selecting its relation value and confirming — at which point dbbro
displays that related record the same way, following the relation's declared
local/foreign column mapping.

## 2. Goals

- Show every configured column of a matched record, labeled with the owning
  table's name, in a table layout.
- Make it visually unambiguous when a column's value is a relation to another
  table rather than a plain value.
- Let the operator move a selection cursor among a record's fields using the
  Up and Down keys.
- Let the operator follow a selected relation to the related record's own
  table view by pressing Return.

## 3. Out of scope

- Finding the initial matched record (covered by EP-2 — Record Search).
- Remembering or navigating between previously visited table views (covered
  by EP-4 — Browsing History).
- Reporting or recovering from a failed relation lookup (covered by EP-5 —
  Error Reporting).
- Editing any field's value from the table view.
- Deciding the on-screen character set, layout technology, or rendering
  approach used to draw the table (already illustrated in the briefing as an
  example only).

## 4. Personas

- **Operator** — has just searched for a record (EP-2) and now wants to read
  its fields and, when relevant, pivot to a related record without leaving
  the keyboard.
- **End user** — same as Operator in this epic; dbbro has a single kind of
  interactive user browsing the database through the table view.

## 5. Domain concepts

- **Record** — a single row of a table, uniquely identified by its primary
  key value (as declared in EP-1's configuration), that is being displayed.
- **Field** — one column of the displayed record's table paired with that
  record's value for the column. A record has exactly one field per column
  declared for its table in the configuration.
- **Relation field** — a field whose column is the local column of a
  declared relation (EP-1). Its displayed value takes the form
  `<related table name>[<foreign key value>]` instead of the column's raw
  stored value, where `<related table name>` is the relation's target table
  and `<foreign key value>` is the value found in the record's local column.
  A relation field also displays the relation's configured label (e.g.
  "belongs to company") alongside its column name, and is rendered with a
  visually distinct style from a plain field so it is recognizable even
  before reading its value. A table may declare more than one relation, and
  each relation's local column is its own independent relation field.
- **Selection** — exactly one field of the currently displayed record is
  selected at a time; moving Up or Down changes which field is selected,
  wrapping from the last field back to the first (and vice versa) rather
  than stopping at either end. When a table view has more fields than fit
  on screen, moving the selection scrolls the view as needed to keep the
  selected field visible.
- **Table view** — the full on-screen presentation of one record: the
  table's name, and every one of its fields with its column name and
  (possibly relation-formatted) value. A primary key column may itself be a
  relation's local column, in which case it is displayed and navigable like
  any other relation field.
- **Navigation** — the act of pressing Return while a relation field is
  selected, which looks up the related record by matching the relation's
  foreign column against the foreign key value shown. If exactly one record
  matches, the current table view is replaced with a new table view of that
  related record, with its first field initially selected. If more than one
  record matches, dbbro presents a selection list of the matching records
  for the operator to choose from before displaying one as a table view. If
  zero records match, dbbro surfaces the failure through the error-notice
  mechanism (EP-5) instead of displaying a table view.
- **Breadcrumb** — a running display of the sequence of table views visited
  since the operator's current search, shown alongside the table view, that
  lets the operator see the path taken to reach the record currently on
  screen.

## 6. User journeys

### 6.1 Operator views a matched record
The operator has just found a record via search (EP-2). dbbro displays a
table view: the table name, every configured column of that table with its
value, and a breadcrumb showing this as the first stop on the current path.
Non-relation fields show their stored value as-is.

### 6.2 Operator identifies a relation field
While looking at a table view, the operator notices a field rendered in a
visually distinct style, showing its column name together with the
relation's configured label and a value in the `<table name>[<foreign key
value>]` form rather than a plain value, indicating it is a relation to
another table rather than an ordinary column.

### 6.3 Operator moves the selection
The operator presses Up or Down to move the selection from one field to the
next or previous field in the record. If the operator presses Down while the
last field is selected, the selection wraps to the first field (and
symmetrically for Up on the first field). If the table view has more fields
than fit on screen, the view scrolls automatically to keep the selected
field visible.

### 6.4 Operator follows a relation
With a relation field selected, the operator presses Return. dbbro looks up
the related record using the relation's local/foreign column mapping.
- If exactly one record matches, dbbro displays that related record as a new
  table view, replacing the one on screen, following the same layout rules
  as 6.1, with its first field initially selected, and extends the
  breadcrumb with this new stop.
- If more than one record matches, dbbro presents a selection list of the
  matching records; once the operator picks one, it is displayed as a new
  table view the same way.
- If zero records match, dbbro surfaces the failure through the error-notice
  mechanism (EP-5) and the current table view remains on screen.

### 6.5 Operator selects a non-relation field and presses Return
The operator has a non-relation field selected and presses Return. Nothing
happens — Return only triggers navigation when a relation field is selected.

## 7. Functional requirements

### Display
1. Given a matched record, the system must display every column declared for
   that record's table in the configuration, together with that record's
   value for each column. If a table declares more than one relation, each
   relation's local column is displayed as its own independent field.
2. The displayed table view must be labeled with the name of the record's
   table.
3. For a field whose column is the local column of a declared relation, the
   system must display the value as `<related table name>[<foreign key
   value>]` instead of the column's raw stored value, display the relation's
   configured label alongside the column name, and render the field in a
   visually distinct style from a plain field. This applies uniformly even
   when the relation's local column is the table's primary key.
4. For a field whose column is not the local column of any declared
   relation, the system must display the column's stored value unchanged.
5. The system must display a breadcrumb, alongside the table view, listing
   the sequence of table views visited since the current search, ending with
   the record currently on screen.

### Selection
6. The system must let the operator move a single-field selection cursor up
   and down among the record's displayed fields using the Up and Down keys,
   wrapping from the last field to the first field (and from the first field
   to the last) rather than stopping at either end.
7. Exactly one field of the displayed record is selected at any time while a
   table view is on screen.
8. When a table view has more displayed fields than fit on screen, moving
   the selection must scroll the view as needed to keep the selected field
   visible.

### Navigation
9. When the operator presses Return while a relation field is selected, the
   system must look up the related record(s) using that relation's declared
   local column (on the current record) and foreign column (on the target
   table).
10. When exactly one related record is found, the system must display it as
    a new table view, following the same Display requirements (FR1–FR5) as
    the record it was navigated from, with its first field initially
    selected, and extend the breadcrumb with this new table view.
11. When more than one related record is found, the system must present a
    selection list of the matching records; once the operator selects one,
    it must be displayed as a new table view following FR10.
12. When zero related records are found, the system must surface the
    failure through the error-notice mechanism (EP-5) and leave the current
    table view on screen.
13. Pressing Return while a non-relation field is selected must not trigger
    any navigation.

## 8. Non-functional requirements

1. Displaying a table view for a matched or navigated-to record must not
   require the operator to take any action beyond the triggering key press
   (search submission, Return on a relation field, or a selection made from
   a multi-match list).
2. The relation-value format (`<related table name>[<foreign key value>]`),
   the accompanying relation label, and the distinct relation styling must
   be applied consistently for every relation field, across every table, so
   the operator can always recognize a relation field by its shape alone.
3. Column order within a table view must be consistent and predictable for
   the same table across displays, so the operator can rely on field
   position when repeatedly browsing the same kind of record.
4. Scrolling a table view to keep the selected field visible must reuse the
   existing Up/Down selection input, without introducing a second,
   independent navigation scheme for scrolling.

## 9. Acceptance criteria

### Display
- AC1. Given a matched record, dbbro displays a table view listing every
  column configured for that record's table, each paired with its value, and
  labeled with the table's name.
- AC2. Given a field whose column is a relation's local column, dbbro
  displays its value as `<related table name>[<foreign key value>]`,
  displays the relation's configured label alongside the column name, and
  renders the field in a visually distinct style from a plain field — even
  when that column is the table's primary key.
- AC3. Given a field whose column is not a relation's local column, dbbro
  displays the column's stored value without any relation formatting.
- AC4. Given a table declares two or more relations, dbbro displays each
  relation's local column as its own independent, separately formatted
  field.
- AC5. Given any table view is displayed, dbbro shows a breadcrumb listing
  the table views visited since the current search, ending with the record
  on screen.

### Selection
- AC6. Given a table view is displayed, exactly one field is selected, and
  pressing Down moves the selection to the next field, wrapping to the first
  field if the last field was selected.
- AC7. Given a table view is displayed, pressing Up moves the selection to
  the previous field, wrapping to the last field if the first field was
  selected.
- AC8. Given a table view has more fields than fit on screen, moving the
  selection with Up or Down scrolls the view to keep the selected field
  visible.

### Navigation
- AC9. Given a relation field is selected and the operator presses Return,
  and exactly one record matches, dbbro displays a new table view for that
  related record, resolved via the relation's local/foreign column mapping,
  with its first field initially selected, and the breadcrumb extended with
  this new table view.
- AC10. Given a non-relation field is selected and the operator presses
  Return, the currently displayed table view remains unchanged.
- AC11. Given a relation field whose local column value matches more than
  one record in the target table, dbbro presents a selection list of the
  matching records, and displays the operator's chosen record as a new table
  view per AC9.
- AC12. Given a relation field whose local column value matches zero records
  in the target table, dbbro surfaces the failure through the error-notice
  mechanism (EP-5) and leaves the current table view on screen unchanged.

## 10. Dependencies and assumptions

- Depends on EP-1 (Schema Configuration) for the declared columns, primary
  keys, and relations (local column, foreign column, label) used to build
  each table view.
- Depends on EP-2 (Record Search) to produce the initial matched record that
  this epic's table view displays.
- Assumes the underlying record data (both the initially matched record and
  any related record) is reachable once a match or relation lookup succeeds;
  failure handling itself belongs to EP-5 (Error Reporting).
- EP-4 (Browsing History) depends on this epic's table views being the units
  that get added to history.
- This epic's breadcrumb (FR5/AC5) is a lightweight, session-local display of
  the path taken since the current search; it does not implement back/forth
  navigation or persist history for reuse across searches — that remains
  EP-4's exclusive responsibility. EP-4 may choose to reuse or replace this
  epic's path-tracking data when implementing full history; the two features
  are expected to be reconciled during EP-4's implementation.

## 11. Open questions

_None — all open questions from Cycle 0 were resolved in Cycle 1 (see
Decision log)._

## 12. Decision log

### Cycle 1 — answered
| #   | Question | Decision |
| --- | -------- | -------- |
| Q1  | Selection behavior at first/last field on Up/Down | Selection wraps around to the opposite end |
| Q2  | Relation lookup with zero matching records | Treat it as an error and surface it through the error-notice mechanism (EP-5) |
| Q3  | Relation lookup with more than one matching record | Present a selection list of all matching records for the operator to choose from |
| Q4  | Whether the relation's configured label appears in the table view | Yes — shown alongside the column name for relation fields |
| Q5  | Whether a table can have multiple independent relation fields | Yes — each is its own independent field with its own relation formatting |
| Q6  | How a table view with more fields than fit on screen is viewed | The table view scrolls, and Up/Down selection movement scrolls it automatically to keep the selected field visible |
| Q7  | Initial selection after navigating to a related record | The first field of the new record |
| Q8  | Whether a primary key column can be a relation's local column | Yes, if EP-1's configuration declares such a relation, it behaves like any other relation field |
| Q9  | Whether the operator needs an indication of the path taken to the current record | Yes — a breadcrumb of the path taken so far is shown alongside the table |
| Q10 | Whether relation fields are visually distinguished beyond the value format | Yes — relation fields are shown in a visually distinct style in addition to the value format |
