# Roadmap: Console Database Browser (dbbro)

Deliver a terminal application that lets an operator search, view, and navigate
related records in a relational database using a schema defined entirely in a
configuration file, with no generic/free-form query capability.

---

## Dependency graph

| Epic | Depends on             | Can start in parallel with |
| ---- | ---------------------- | -------------------------- |
| Epic | Depends on                  | Can start in parallel with |
| ---- | --------------------------- | -------------------------- |
| EP-1 | —                           | EP-6                       |
| EP-6 | EP-1                        | —                          |
| EP-2 | EP-1, EP-6                  | —                          |
| EP-3 | EP-1, EP-2, EP-6            | EP-5                       |
| EP-4 | EP-1, EP-2, EP-3, EP-6      | EP-5                       |
| EP-5 | EP-1, EP-2, EP-6            | EP-3, EP-4                 |
| EP-7 | EP-1, EP-2, EP-3, EP-5, EP-6 | EP-4                       |

EP-6 (Database Connection Configuration) is new: EP-2's search lookups and
EP-3's relation lookups both require an established database connection to
actually run a query, so both now depend on EP-6 in addition to their
existing dependencies. EP-6 itself only depends on EP-1, since it extends
the same configuration file with a `database` section rather than
introducing a second config mechanism.

EP-7 (Terminal Rendering) is new: it depends on EP-2, EP-3, and EP-5
because it must actually draw every screen those epics defined (search
dialog, value prompt, table view, match list, error notice) — it has
nothing to render until those screens exist. It does not depend on EP-4,
since browsing history reuses EP-2/EP-3's existing screens rather than
introducing a new one, so EP-7 can proceed in parallel with EP-4.

---

## EP-1 — Schema Configuration

An operator can describe the tables that dbbro is allowed to browse in a
configuration file before running the app: which columns each table has,
which of those columns are searchable, which column is the primary key, and
how tables relate to one another (including a human-readable label for each
relation). dbbro reads this configuration on startup and refuses to run
against a table, column, or relation that is not declared in it.

**Acceptance criteria**

- Given a configuration file listing tables with their columns, search
  columns, primary key, and relations, dbbro loads it successfully on startup.
- A table's searchable columns are exactly the columns listed under its
  `search_columns` entry — no other column is offered for searching.
- A relation between two tables is defined by a local column, a foreign
  column, and a display label, and dbbro uses that label when presenting the
  relation to the user.
- If the configuration is missing, unreadable, or structurally invalid,
  dbbro reports an error identifying the problem instead of starting.

---

## EP-6 — Database Connection Configuration

An operator can declare, in the same configuration file used for the
schema, how dbbro should connect to the actual database — host, database
name, and user — without the password needing to live in that file.

**Acceptance criteria**

- Given a configuration file with a `database` section specifying host,
  database name, user, and password, dbbro connects to that database on
  startup using those values.
- Given a `database` section that omits the password, dbbro reads the
  password from the `DBBRO_DB_PWD` environment variable instead.
- Given a `database` section missing a required value (host, database name,
  or user) with no password available from either the file or the
  environment variable, dbbro reports an error identifying the missing
  piece instead of starting.
- Given a valid `database` section but a connection that cannot be
  established (e.g. unreachable host, rejected credentials), dbbro reports
  an error describing the connection failure instead of starting.

---

## EP-2 — Record Search

An operator can search for a specific record at any time: choose which
table/column combination to search on, then type the value to look for.

**Acceptance criteria**

- On startup, dbbro presents a list of every searchable table/column pair
  drawn from the configuration.
- The operator selects one pair by moving up and down through the list.
- After selecting a pair, the operator is prompted to enter a search value
  for that column.
- Submitting a search value looks up the matching record in that table.
- The search selection dialog can be reopened at any point in the
  application by pressing the `s` key.

---

## EP-3 — Entry Table View

When a search finds a record, the operator sees its fields laid out as a
table, including any related records, and can jump to a related record by
selecting it.

**Acceptance criteria**

- Given a matched record, dbbro displays every configured column of that
  record's table alongside its value, labeled with the table name.
- A column value that represents a relation to another table is shown in
  the form `<related table name>[<foreign key value>]` rather than the raw
  key.
- The operator can select a relation value by moving up and down among the
  record's fields.
- Pressing Return while a relation value is selected opens the related
  record's own table view, following that relation's local/foreign column
  mapping.

---

## EP-4 — Browsing History

An operator can move backward and forward through the sequence of record
views they have visited, the same way browser history works.

**Acceptance criteria**

- Each time a new record's table view is displayed, it is added to the
  browsing history.
- Pressing the Left key returns to the previously viewed table view.
- Pressing the Right key moves forward again to the table view that was
  left via the Left key.
- Opening the search dialog or entering a search value does not by itself
  create a history entry — only the resulting table view does.

---

## EP-5 — Error Reporting

An operator is clearly informed when something goes wrong — for example, a
search that cannot be completed or a lookup that fails — and can dismiss the
notice and keep working.

**Acceptance criteria**

- When an operation such as a search or a relation lookup fails, dbbro
  shows a modal error notice describing the problem.
- The error notice remains on screen until the operator presses Return.
- Pressing Return closes the error notice and returns the operator to the
  view they were on before the error occurred.

---

## EP-7 — Terminal Rendering

An operator actually sees dbbro's screens drawn in the terminal — the
search selection dialog, the search value prompt, the table view, the
match/selection list, and the error notice — instead of a blank screen,
using the panel and modal box-drawing styles described in the briefing.

**Acceptance criteria**

- The search selection dialog is drawn as a modal box (double-line border)
  listing each table/column pair, with the currently highlighted pair
  visually distinguished from the others.
- The search value prompt is drawn as a modal box (double-line border)
  showing the selected table/column label alongside the text the operator
  has typed so far.
- A record's table view is drawn as a bordered panel (single-line border)
  with one row per configured column, each row showing the column name and
  its value, labeled with the table name.
- Within a drawn table view, the field the operator has selected is
  visually distinguished from the others, and a relation field's value is
  shown in the `<related table name>[<foreign key value>]` format.
- When a search or relation lookup matches more than one record, the
  resulting match/selection list is drawn the same way — one row per
  candidate record — with the currently highlighted row visually
  distinguished.
- The error notice is drawn as a modal box (double-line border) describing
  the problem, remaining visible until the operator presses Return.
- Whichever screen is currently active is the only one visibly drawn; no
  screen is left rendering stale or overlapping content from a screen that
  is no longer active.
