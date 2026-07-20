# Epic 3 — Entry Table View — Technical Specification

Tech spec for `3_entry_table_view.md`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~95% after revision 2 — D1–D3 are now resolved and folded into §3/§6/§7, and Epic 2's independently-written spec confirms the same `curses` foundation; the only remaining gap is external to this spec — Epic 4's spec recommended `prompt_toolkit` instead of `curses`, a cross-epic conflict that must be reconciled before implementation but does not by itself block starting T1 here.

## 1. Overview

This spec covers displaying a matched or navigated-to record as a two-column table view in dbbro's terminal UI: rendering every configured column of a record's table with its value, formatting and highlighting relation fields, letting the operator move a selection cursor with Up/Down (with wraparound and auto-scroll), following a selected relation via Return (including the zero/one/many-match outcomes), and showing a breadcrumb of the path taken. Out of scope: producing the initial matched record (EP-2), remembering/navigating history across table views (EP-4), and rendering the error-notice popup itself (EP-5, though this epic triggers it). See `3_entry_table_view.md`.

**Assumption (not in the PRD):** because no prior epic had introduced any UI or database-access code at the time this spec was first written, this spec also laid the minimal shared foundations (terminal UI library, DB query layer) that Epic 2 needed too. Epic 2's own spec (`2_record_search-spec.md`) has since independently settled on the same `curses` foundation, confirming rather than contradicting D1's resolution below.

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| FR1  | Display every configured column + value, incl. multiple independent relation fields | §3, §4, §6 T2 |
| FR2  | Table view labeled with table name | §3, §6 T2 |
| FR3  | Relation field shows `<table>[<fk>]`, relation label, distinct style, even for PK | §4, §6 T3 |
| FR4  | Non-relation field shows raw stored value | §4, §6 T2 |
| FR5  | Breadcrumb shown alongside table view | §3, §6 T7 |
| FR6  | Up/Down moves selection, wraps at ends | §3, §6 T4 |
| FR7  | Exactly one field selected at a time | §4, §6 T4 |
| FR8  | Scrolling keeps selected field visible when overflowing screen | §3, §6 T5 |
| FR9  | Return on relation field looks up related record via local/foreign mapping | §3, §6 T6 |
| FR10 | Exactly one match → new table view, first field selected, breadcrumb extended | §6 T6 |
| FR11 | More than one match → selection list, then FR10 | §6 T8 |
| FR12 | Zero matches → EP-5 error notice, current view unchanged | §6 T6 |
| FR13 | Return on non-relation field does nothing | §6 T6 |
| NFR1 | No extra action needed beyond the triggering key press | §3, §6 T6 |
| NFR2 | Relation formatting/label/style consistent across every field/table | §4, §6 T3 |
| NFR3 | Column order consistent and predictable per table | §4, §6 T2 |
| NFR4 | Scrolling reuses Up/Down, no second scheme | §3, §6 T5 |
| AC1  | Table view lists every configured column + value, labeled with table name | §6 T2 |
| AC2  | Relation field format/label/style, incl. PK case | §6 T3 |
| AC3  | Non-relation field shows raw value | §6 T2 |
| AC4  | Two+ relations each shown as independent fields | §6 T3 |
| AC5  | Breadcrumb shown, ending with current record | §6 T7 |
| AC6  | Down wraps last→first | §6 T4 |
| AC7  | Up wraps first→last | §6 T4 |
| AC8  | Overflow scrolls to keep selection visible | §6 T5 |
| AC9  | Single match → new table view, first field selected, breadcrumb extended | §6 T6 |
| AC10 | Return on non-relation field → no change | §6 T6 |
| AC11 | Multi-match → selection list → AC9 | §6 T8 |
| AC12 | Zero matches → EP-5 error, current view unchanged | §6 T6 |

## 3. Architecture

```
dbbro/
  config/            # (existing, Epic 1)
  db/
    __init__.py
    connection.py    # open a DB-API 2.0 connection from a connection string/path
    queries.py        # fetch_by_primary_key(conn, table, pk_col, pk_value) -> Row | None
                       # fetch_by_column_equals(conn, table, column, value) -> list[Row]
                       #   (used by both this epic's relation lookup and EP-2's search lookup)
  navigation/
    __init__.py
    breadcrumb.py     # Breadcrumb: push(stop) / reset() / as_list()
  ui/
    __init__.py
    app.py            # curses.wrapper entry point, main event loop, key dispatch
    table_view.py      # renders one record as a two-column field table + breadcrumb strip
    fields.py          # Field / RelationField view-model construction from a Row + Table + Relations
    selection_list.py  # modal list used for multi-match relation resolution (and reused by EP-2)
  cli.py               # existing; run_ui(config) wired to ui.app.run(config)
```

Flow: `cli.py::run_ui(config)` opens a DB connection (`db.connection`) and calls `ui.app.run(config, conn)`, which enters a `curses.wrapper`-managed loop. Once EP-2 hands this epic a matched `(table_name, primary_key_value)`, `ui.app` calls `db.queries.fetch_by_primary_key` to load the row, builds `fields.py`'s list of `Field`/`RelationField` view-models from the row plus the `Table`'s declared `columns`/`relations` (column order == `Table.columns` order, satisfying NFR3), pushes a stop onto `navigation.breadcrumb.Breadcrumb`, and renders via `ui.table_view`. Up/Down key events update a selection index (mod `len(fields)`, giving wraparound for FR6/AC6/AC7) and recompute a scroll offset so the selected row's screen line stays within the visible window (FR8/AC8/NFR4 — same key events drive both selection and scroll, no separate scroll keys). Return, when the selected field is a `RelationField`, calls `db.queries.fetch_by_column_equals(conn, relation.target_table, relation.foreign_column, field.raw_value)`: zero rows raises the EP-5 error-notice trigger (this epic calls an `on_lookup_error(message)` hook, presumed to exist per EP-5's contract) and leaves the current view untouched; exactly one row repeats the "build fields, push breadcrumb, render" flow for the new record with field index reset to 0; more than one row opens `ui.selection_list` (Up/Down + Return to pick, Escape not specified for this flow per PRD out-of-scope) and, once one is chosen, proceeds exactly as the one-row case. Return on a non-`RelationField` is a no-op (FR13/AC10).

**Key architecture decisions:**

- **Terminal UI is built on stdlib `curses` (D1)** — no additional dependency, and the widget set this epic needs (box-drawn table, one modal list, auto-scroll) is small enough to hand-roll; this becomes the shared UI foundation Epic 2 (search dialogs) and Epic 4 (breadcrumb/history) build on. *(Architecture advisor: keeps the zero-third-party-dependency posture the project already has with only pyyaml, and avoids Textual's async model that nothing else in the codebase uses.)*
- **Database access is a thin DB-API 2.0 layer with a small hand-written parameterized query builder (D2)**, starting with `sqlite3`, not an ORM or SQLAlchemy — table/column names are only known at runtime from the YAML config (`config/models.py`), so there are no static model classes to map, and every query this epic needs is a single-table equality-filtered SELECT. *(Architecture advisor: an ORM/expression-builder buys nothing when schemas are dynamic and only simple SELECTs are needed; this also directly serves EP-2's reuse of the same `fetch_by_column_equals` lookup.)*
- **The breadcrumb is a small standalone `Breadcrumb` class in a new `dbbro/navigation/` module (D3)**, not inline app-state and not derived from the call stack — deliberately separate from whatever `History` class EP-4 introduces later, per the PRD's explicit note that the two are "reconciled during EP-4's implementation." *(Architecture advisor: matches the project's existing convention — seen in `dbbro/config/` — of giving each concern its own module with a narrow surface, and keeps EP-4 free to reuse or replace this data structure without EP-3's code assuming it will.)*
- **Field view-models are built once per record display, not re-derived per keystroke** — `fields.py` produces an immutable list of `Field`/`RelationField` objects from a `Row` + `Table` + its `relations` tuple at render time; Up/Down only moves an index into that already-built list, keeping key-handling O(1) and side-effect-free.
- **Relation lookup failures surface via a caller-supplied error hook rather than this epic raising its own exception type** — since EP-5's exact error-notice mechanism/API is specified by a separate epic, `ui/app.py` calls a single narrow seam (`on_lookup_error(message: str) -> None`) so EP-5's implementation can be slotted in without this epic needing to know its internals.

## 4. Data model

`dbbro/ui/fields.py` (session-local view-models, not persisted):

- `Field`: `column: str`, `value: str` (the raw stored value, stringified for display).
- `RelationField(Field)`: adds `label: str` (the relation's configured label), `related_table: str`, `foreign_key_value: str`; its `value` is rendered as `f"{related_table}[{foreign_key_value}]"` per FR3. A table's `RelationField`s are derived one-per-relation from `Table.relations`, so a table with two or more relations produces two or more independent `RelationField`s (FR1/AC4), even when a relation's `local_column` equals `Table.primary_key` (FR3/AC2).
- Field ordering follows `Table.columns` order exactly (NFR3); for each column, if it is some relation's `local_column`, a `RelationField` is built for it, else a plain `Field`.

`dbbro/navigation/breadcrumb.py`:

- `BreadcrumbStop`: `table: str`, `primary_key_value: str` — enough to label a breadcrumb entry (table name) and re-identify the stop.
- `Breadcrumb`: holds `stops: list[BreadcrumbStop]`; `push(stop)` appends, `reset()` clears (called when a new search, per EP-2, produces a fresh matched record), `as_list() -> list[BreadcrumbStop]` for rendering — no undo/index/navigation methods, kept deliberately minimal per the architecture-advisor's note.

`dbbro/db/queries.py`:

- `Row = dict[str, Any]` — a mapping of column name to stored value for one database row, keyed by every column in `Table.columns`.

## 5. API / interfaces

`dbbro/db/connection.py`:
```python
def connect(dsn: str) -> Connection:
    """Open a DB-API 2.0 connection (sqlite3 to start)."""
```

`dbbro/db/queries.py`:
```python
def fetch_by_primary_key(conn, table: Table, pk_value: str) -> Row | None: ...
def fetch_by_column_equals(conn, table: Table, column: str, value: str) -> list[Row]: ...
```

`dbbro/ui/fields.py`:
```python
def build_fields(table: Table, row: Row) -> list[Field]: ...
```

`dbbro/navigation/breadcrumb.py`:
```python
class Breadcrumb:
    def push(self, stop: BreadcrumbStop) -> None: ...
    def reset(self) -> None: ...
    def as_list(self) -> list[BreadcrumbStop]: ...
```

`dbbro/ui/app.py` (consumed by `cli.py::run_ui`):
```python
def run(config: Config, conn, initial_table: str, initial_pk_value: str, on_lookup_error) -> None:
    """Enter the curses event loop, starting on the record identified by
    (initial_table, initial_pk_value) — the record EP-2 has just matched.
    `on_lookup_error(message: str)` is EP-5's seam for the zero-match case.
    """
```

## 6. Implementation plan (TDD)

### T1. DB connection + query layer                (closes: — infrastructure for FR9/FR12)
- Failing tests to write first:
  - `test_fetch_by_primary_key_returns_row_when_found`
  - `test_fetch_by_primary_key_returns_none_when_missing`
  - `test_fetch_by_column_equals_returns_all_matching_rows`
  - `test_fetch_by_column_equals_returns_empty_list_when_no_match`
- Production code to make them pass:
  - `db/connection.py::connect`
  - `db/queries.py::fetch_by_primary_key`, `fetch_by_column_equals`

### T2. Build and render a table view for a matched record        (closes: FR1, FR2, FR4, NFR3, AC1, AC3)
- Failing tests to write first:
  - `test_build_fields_orders_fields_by_table_columns_order`
  - `test_build_fields_plain_column_shows_raw_value`
  - `test_table_view_renders_table_name_label`
- Production code to make them pass:
  - `ui/fields.py::build_fields` (plain-field branch)
  - `ui/table_view.py::render` (curses rendering of table name + rows)

### T3. Relation field formatting and styling         (closes: FR3, NFR2, AC2, AC4)
- Failing tests to write first:
  - `test_build_fields_relation_column_uses_related_table_bracket_fk_format`
  - `test_build_fields_relation_column_includes_configured_label`
  - `test_build_fields_relation_on_primary_key_still_formatted_as_relation`
  - `test_build_fields_two_relations_produce_two_independent_relation_fields`
- Production code to make them pass:
  - `ui/fields.py::build_fields` (relation-field branch), `RelationField`
  - `ui/table_view.py::render` (distinct style for `RelationField` rows)

### T4. Selection cursor with Up/Down wraparound              (closes: FR6, FR7, AC6, AC7)
- Failing tests to write first:
  - `test_selection_moves_down_to_next_field`
  - `test_selection_wraps_from_last_to_first_on_down`
  - `test_selection_wraps_from_first_to_last_on_up`
  - `test_exactly_one_field_selected_at_a_time`
- Production code to make them pass:
  - `ui/app.py`'s selection-index state and Up/Down key handlers

### T5. Auto-scroll to keep selection visible          (closes: FR8, NFR4, AC8)
- Failing tests to write first:
  - `test_scroll_offset_advances_when_selection_moves_past_visible_window`
  - `test_scroll_offset_unchanged_when_selection_stays_within_visible_window`
  - `test_no_separate_scroll_keys_needed_up_down_alone_scrolls`
- Production code to make them pass:
  - `ui/table_view.py`'s scroll-offset computation, driven by the same Up/Down handlers as T4

### T6. Navigate on Return: single match, zero match, non-relation no-op        (closes: FR9, FR10, FR12, FR13, NFR1, AC9, AC10, AC12)
- Failing tests to write first:
  - `test_return_on_relation_field_with_one_match_displays_new_table_view_with_first_field_selected`
  - `test_return_on_relation_field_with_one_match_extends_breadcrumb`
  - `test_return_on_relation_field_with_zero_matches_calls_on_lookup_error_and_keeps_current_view`
  - `test_return_on_non_relation_field_does_nothing`
- Production code to make them pass:
  - `ui/app.py`'s Return handler: dispatch on selected-field type and `fetch_by_column_equals` result length

### T7. Breadcrumb display                        (closes: FR5, AC5)
- Failing tests to write first:
  - `test_breadcrumb_push_appends_stop`
  - `test_breadcrumb_as_list_ends_with_current_record`
  - `test_table_view_renders_breadcrumb_alongside_table`
- Production code to make them pass:
  - `navigation/breadcrumb.py::Breadcrumb`
  - `ui/table_view.py::render` (breadcrumb strip)

### T8. Multi-match selection list on relation follow          (closes: FR11, AC11)
- Failing tests to write first:
  - `test_return_on_relation_field_with_multiple_matches_opens_selection_list`
  - `test_choosing_from_selection_list_displays_new_table_view_per_t6`
- Production code to make them pass:
  - `ui/selection_list.py::run` (modal list, Up/Down + Return)
  - `ui/app.py` wiring from T6's multi-match branch into `selection_list.run`

### Refactor step (after T8)
- Once T2–T8 are green, review `ui/app.py`'s Return handler and `ui/table_view.py`'s render/scroll logic for duplication between the initial-record path and the navigated-to-record path; extract a shared `display_record(table, pk_value)` helper if the two paths have converged to near-identical code.

## 7. Non-functional concerns

- **Single-action navigation (NFR1):** every transition (search submission from EP-2, Return on a relation field, or a selection-list pick) results in a new table view with no further operator input required; enforced by T6/T8's tests asserting the new view renders immediately after the triggering key event.
- **Consistent relation styling (NFR2):** `RelationField` is a distinct type from `Field`, so `ui/table_view.py::render` can dispatch styling by type rather than per-table special-casing, guaranteeing uniform treatment across every table (T3).
- **Predictable column order (NFR3):** `build_fields` iterates `Table.columns` in declared order, never re-sorting or grouping relations separately, so the same table always renders fields in the same order (T2).
- **No parallel scroll scheme (NFR4):** scroll offset is a pure function of the current selection index and viewport height, recomputed inside the same Up/Down handlers as selection movement — there is no separate PageUp/PageDown or scroll-only key path (T5).
- **DB portability:** `db/connection.py` targets DB-API 2.0 generically (starting with `sqlite3`); `queries.py` must use the connected driver's `paramstyle` rather than hardcoding `?`, so swapping the underlying engine later doesn't require rewriting query construction.

## 8. Risks & mitigations

- Risk: hand-rolled curses redraw/scroll logic is more error-prone than a widget-framework's built-in list/table widget. Mitigation: keep `ui/table_view.py`'s render and scroll math isolated and unit-testable independent of the real curses window (inject a fake window/renderer in tests), per T2/T5.
- Risk: this spec designed UI/DB foundations before Epic 2 had its own spec, risking divergence. Mitigation: resolved — Epic 2's spec independently settled on the same `curses` foundation; `db/queries.py` and `ui/selection_list.py` remain generically named and reusable so Epic 2 can import them directly rather than duplicating. Epic 4's spec, however, recommended `prompt_toolkit` instead of `curses` — that cross-epic conflict still needs reconciling before implementation, separately from this spec.
- Risk: `on_lookup_error` is a seam into EP-5, which is not yet specified either — its exact signature may need to change once EP-5's spec is written. Mitigation: keep the seam to a single narrow callback parameter in `ui/app.py::run`, minimizing the blast radius of a signature change.
- Risk: sqlite3's `?` paramstyle is hardcoded as the initial target; a future non-sqlite DSN would break `queries.py` if paramstyle isn't parameterized early. Mitigation: called out explicitly in §7 as a must-fix-before-swap concern, not deferred silently.

## 9. Open architecture decisions

_None — D1–D3 were resolved in Cycle 1; see §10 Decision log. §3, §6, and §7 already reflect all three._

**D1 (resolved):** Which terminal UI library should dbbro use for panels, modals, selection lists, and keyboard-driven navigation? → stdlib `curses`, per Cycle 1. *(Architecture advisor: keeps the project's current zero-third-party-dependency posture intact and avoids Textual's async model, which nothing else in this synchronous codebase uses.)*

**D2 (resolved):** What should the data-access layer for record-by-primary-key and relation-by-foreign-column lookups be built on? → Raw DB-API 2.0 connections (`sqlite3` to start) with a small hand-written parameterized query builder, per Cycle 1. *(Architecture advisor: an ORM or SQLAlchemy Core buys nothing when schemas are dynamic and only simple SELECTs are ever needed, and this directly serves EP-2's reuse of the same lookup function.)*

**D3 (resolved):** What should own Epic 3's breadcrumb (the ordered list of table views visited since the current search)? → A dedicated `Breadcrumb` class in a new `dbbro/navigation/` module, kept separate from any future `History` class, per Cycle 1. *(Architecture advisor: a named, addressable module boundary is what lets EP-4 "reuse or replace this epic's path-tracking data," per the PRD's own §10 reconciliation note, without touching EP-3's call sites.)*

## 10. Decision log

### Cycle 1 — answered
| #  | Question | Decision |
| -- | -------- | -------- |
| D1 | Which terminal UI library should dbbro use for panels, modals, selection lists, and keyboard-driven navigation? | stdlib `curses` |
| D2 | What should the data-access layer for record-by-primary-key and relation-by-foreign-column lookups be built on? | Raw DB-API 2.0 connections (`sqlite3` to start) with a small hand-written parameterized query builder |
| D3 | What should own Epic 3's breadcrumb? | A dedicated `Breadcrumb` class in a new `dbbro/navigation/` module, kept separate from any future `History` class |
