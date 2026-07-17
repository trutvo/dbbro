# Epic 1 — Schema Configuration

PRD for Schema Configuration. Requirements only — no technical or architectural decisions.

> **Confidence:** ~90% after Cycle 1 (re-scored under the new PRD/spec-aware brainstorm skill, still no document changes) — all domain ambiguities (primary key, duplicates, self-relations, labels, error reporting) resolved; remaining gap is NFR2's error-clarity wording ("clearly enough to locate the problem") still being qualitative rather than a concrete, testable format.

## 1. Summary

Before dbbro can be used to browse a database, an operator must describe the
shape of that database in a configuration: which tables exist, which columns
each table has, which columns can be searched, each table's primary key, and
how tables relate to one another. dbbro reads this configuration on startup
and uses it as the sole source of truth for what can be browsed — it never
infers schema from the database itself.

## 2. Goals

- Let an operator declare, outside of application code, the exact set of
  tables, columns, searchable columns, primary keys, and relations dbbro is
  allowed to work with.
- Let dbbro load that declaration once at startup and treat it as complete
  and authoritative for the rest of the session.
- Give the operator a clear, specific error when the declaration is missing,
  unreadable, or inconsistent, so they can fix it before browsing begins.

## 3. Out of scope

- Discovering or introspecting a database's real schema automatically.
- Editing the configuration from within the running application.
- Any search, table view, history, or error-popup behaviour that consumes
  this configuration (covered by other epics).
- Deciding the on-disk format, file location, or parsing technology used to
  represent the configuration.

## 4. Personas

- **Operator** — sets up dbbro for a particular database before anyone
  browses it. Knows the database schema and decides what should be visible
  and searchable.
- **End user** — browses the database through dbbro's UI, relying entirely
  on what the operator declared; never edits the configuration directly.

## 5. Domain concepts

- **Table** — a named entity with a fixed, non-empty list of **columns**,
  exactly one of which is designated the **primary key**. Table names are
  unique across the configuration, and column names are unique within a
  table.
- **Search column** — a column of a table that is allowed to be used as a
  search criterion; a subset of the table's columns, possibly empty — a
  table is not required to have any search columns.
- **Relation** — a directed link from one table (the table declaring it) to
  another table (which may be the same table, i.e. a self-relation), defined
  by a **local column** on the declaring table, a **foreign column** on the
  target table, and a human-readable **label** used when presenting the
  relation in the UI. The local column may be any column of the declaring
  table, including its primary key. Labels are unique across the entire
  configuration, not just within one table.
- **Configuration** — the complete collection of table declarations that
  dbbro loads at startup, from a location the operator supplies when
  starting dbbro; the single source of truth for what exists and what is
  browsable.

## 6. User journeys

### 6.1 Operator prepares a configuration
The operator writes a configuration describing each table they want
browsable: its name, its columns, which columns are searchable, its primary
key, and any relations to other tables. They start dbbro.

### 6.2 dbbro loads a valid configuration
dbbro reads the configuration at startup, accepts it, and becomes ready to
present the searchable table/column pairs it declares (consumed by the
Search epic).

### 6.3 dbbro rejects an invalid or missing configuration
The operator starts dbbro, pointing it at a configuration location, and the
configuration is absent or malformed in one or more ways (e.g. a relation
pointing at a table that isn't declared, a primary key that isn't among the
table's columns, a table with no columns, a duplicate table name, a
duplicate column name within a table, or two relations anywhere sharing the
same label). dbbro stops before presenting any UI and reports every problem
it found in that one pass, so the operator can fix them all before trying
again.

## 7. Functional requirements

### Loading
1. The system must load a configuration, from a location the operator
   supplies when starting dbbro, that declares zero or more tables.
2. Each declared table must specify a name, a non-empty list of columns, a
   primary key column, and a (possibly empty) list of search columns.
3. A table is not required to declare any search columns.

### Validation
4. Each search column listed for a table must be one of that table's
   declared columns.
5. Each table must declare exactly one primary key, and it must be one of
   that table's declared columns.
6. Each declared table may specify zero or more relations to other tables,
   including a relation whose target is the declaring table itself.
7. Each relation must specify the target table, a local column (on the
   declaring table), a foreign column (on the target table), and a
   human-readable label. A relation's local column may be any column of the
   declaring table, including its primary key.
8. Both the local column and the foreign column of a relation must be
   declared columns of their respective tables.
9. The target table of a relation must itself be a table declared in the
   configuration.
10. Table names must be unique across the configuration.
11. Column names must be unique within a single table's declared column
    list.
12. Labels must be unique across all relations in the configuration,
    regardless of which tables declare them.
13. When the configuration fails validation in more than one way, dbbro must
    detect and report every violation found in that pass, not only the
    first one encountered.

### Exposure
14. Once loaded, the configuration is treated as complete and unchanging for
    the remainder of the running session.
15. dbbro must expose, to the rest of the application, the full list of
    searchable table/column pairs derived from the configuration.

## 8. Non-functional requirements

1. Configuration loading happens once at startup and must complete before
   any UI is shown.
2. Validation errors must identify which table, column, or relation caused
   the problem clearly enough for the operator to locate and fix it.

## 9. Acceptance criteria

### Loading
- AC1. Given a configuration declaring one or more valid tables, dbbro
  starts successfully and proceeds to its normal UI.
- AC2. Given no configuration is present, dbbro reports an error and does
  not proceed to its normal UI.

### Validation
- AC3. Given a table whose primary key is not among its declared columns,
  dbbro reports an error identifying that table and does not proceed.
- AC4. Given a table with a search column that is not among its declared
  columns, dbbro reports an error identifying that table and column and does
  not proceed.
- AC5. Given a relation whose target table is not declared in the
  configuration, dbbro reports an error identifying the offending relation
  and does not proceed.
- AC6. Given a relation whose local or foreign column is not a declared
  column of the relevant table, dbbro reports an error identifying the
  offending relation and does not proceed.
- AC8. Given a table declared with zero columns, dbbro reports an error
  identifying that table and does not proceed.
- AC9. Given two tables declared with the same name, dbbro reports an error
  identifying the duplicated name and does not proceed.
- AC10. Given a table declared with two columns of the same name, dbbro
  reports an error identifying that table and column name and does not
  proceed.
- AC11. Given two relations anywhere in the configuration that share the
  same label, dbbro reports an error identifying both offending relations
  and does not proceed.
- AC12. Given a relation whose target table is the same as its declaring
  table, dbbro accepts the configuration (a self-relation is not an error).
- AC13. Given a relation whose local column is the declaring table's primary
  key, dbbro accepts the configuration (this is not an error).
- AC14. Given a table with an empty search-column list, dbbro accepts the
  configuration and that table simply contributes no entries to the
  searchable table/column pairs.
- AC15. Given a configuration with more than one distinct validation
  violation (e.g. a bad relation target and a duplicate table name), dbbro's
  error report includes all of them, not just the first found.

### Exposure
- AC7. Given a successfully loaded configuration, the set of searchable
  table/column pairs dbbro exposes matches exactly the search columns
  declared across all tables.

## 10. Dependencies and assumptions

- Assumes a database matching the declared schema is reachable once
  configuration loading succeeds (connection/access mechanics are out of
  scope for this epic).
- The Search epic (EP-2) depends on the searchable table/column pairs this
  epic exposes.
- The Entry Table View epic (EP-3) depends on the column and relation
  declarations this epic validates.

## 11. Open questions

_None outstanding — all Cycle 1 gaps were resolved and reconciled above._

## 12. Decision log

### Cycle 1 — answered

| #   | Question | Decision |
| --- | -------- | -------- |
| Q1  | Is a primary key mandatory for every table? | Every table must declare exactly one primary key column. |
| Q2  | Can a table be declared with zero columns? | Rejected as a configuration error. |
| Q3  | Are duplicate table names across the configuration allowed? | Rejected as a configuration error. |
| Q4  | Are duplicate column names within one table allowed? | Rejected as a configuration error. |
| Q5  | Can two distinct relations share the same label? | Rejected as a configuration error if any two relations anywhere share a label. |
| Q6  | Can a table declare a relation targeting itself? | Allowed. |
| Q7  | Must every table declare at least one search column? | No — a table may have an empty search-column list. |
| Q8  | Can a relation's local column also be that table's primary key? | Allowed. |
| Q9  | Is the configuration's location operator-supplied or fixed? | Operator-supplied when starting dbbro. |
| Q10 | How much does dbbro report when multiple validation errors exist? | Reports all detected errors together in one pass. |
