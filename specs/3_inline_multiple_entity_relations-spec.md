# Epic 3 — Inline Multiple-Entity Relations — Technical Specification

Tech spec for `specs/3_inline_multiple_entity_relations.md`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~92% after revision 2 — the PRD's previously-flagged empty-`search_columns` risk is now closed via F9/AC10's first-column fallback; remaining minor risk is that the concatenation separator and "own value" line format are new, not-yet-executed code paths, though well-justified from the PRD's worked example

## 1. Overview

`TableView` (`dbbro/ui/table_view.py`) currently renders one row per field and, for a relation column, follows Enter to a separate `SelectionList` modal when more than one related record matches. This epic replaces that indirection for *viewing*: every configured relation's matching related records are resolved and rendered as extra rows directly beneath the relation's local column, in the same `draw_panel` panel, with no row-count limit. Following a relation via Enter (pushing a new `TableView` or `SelectionList`) is unchanged and out of scope.

Explicit assumption carried over from the PRD (§10): a related entity is only ever listed when it was matched via a non-null foreign key value, so its identifying value (built from the foreign table's `search_columns`, or its first defined column when none are configured — F9/AC10) is never empty in practice; this spec does not add new validation to guarantee that.

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| F1 | One line per related entity beneath the local column | §3, §6 T2 |
| F2 | Line includes relation's label + identifying value from `search_columns` | §3, §5, §6 T1, T2 |
| F3 | No separate selection list needed to view relations | §3, §6 T2 |
| F4 | Same display for 0, 1, or many related entities | §3, §6 T2, T3 |
| F5 | No upper limit on related entities listed | §3, §6 T2, T4 |
| F6 | Local column's own value shown as first line | §3, §6 T2 |
| F7 | Multiple relations on one local column grouped, in configured order | §3, §4, §6 T2 |
| F8 | Uniform display for every configured relation | §3, §6 T2 |
| F9 | Identifying value falls back to the first defined column when no `search_columns` are configured | §5, §6 T1 |
| N1 | Viewing relations never requires leaving the table view | §3, §6 T2 |
| AC1 | Multiple related entities each on their own line | §6 T2 |
| AC2 | Each line shows label + identifying value | §6 T1, T2 |
| AC3 | No separate selection list needed | §6 T2 |
| AC4 | Single related entity uses same listing as multiple | §6 T3 |
| AC5 | Zero related entities → no lines shown | §6 T3 |
| AC6 | Large number of related entities, no truncation/cap | §6 T4 |
| AC7 | Identifying value built from foreign table's `search_columns` | §6 T1 |
| AC8 | Local column's own value is the first line | §6 T2 |
| AC9 | Two+ relations grouped, in configured order | §6 T5 |
| AC10 | Identifying value uses the first defined column when `search_columns` is empty | §6 T1 |

## 3. Architecture

### Components touched

- `dbbro/ui/table_view.py` (`TableView`) — builds the rows passed to `draw_panel`, currently one row per `Field`.
- `dbbro/ui/fields.py` (`build_fields`, `Field`, `RelationField`) — unchanged. Continues to produce exactly one `Field`/`RelationField` per column, in `Table.columns` order; still used for Up/Down navigation and for the Enter-to-follow flow.
- `dbbro/ui/screen.py` (`draw_panel`) — unchanged. It already renders an arbitrary `list[tuple[str, str]]` of (name, value) rows with a single-line-per-row model, so extra "continuation" rows with an empty name cell (matching the briefing's blank-name-column example) require no changes here.
- New module `dbbro/ui/relation_rows.py` — the only new production code, containing the row-expansion and identifying-value logic.

### Data flow

1. `TableView.__init__` builds `self.fields = build_fields(table, record)` as before.
2. `TableView.__init__` additionally calls `build_display_rows(self.fields, table, config, conn)` (new, in `relation_rows.py`), which:
   - Walks `self.fields` in order (preserving F6/F8's per-column ordering).
   - For a plain `Field`, emits one `(field.column, field.value)` row.
   - For a `RelationField`, emits `(field.column, field.foreign_key_value)` as the first row (the local column's own raw value — see "Key architecture decisions" below), then for every `Relation` in `table.relations` whose `local_column == field.column`, **in `table.relations` order** (closes F7/AC9), fetches matches via the existing `fetch_by_column_equals(conn, target_table, relation.foreign_column, field.foreign_key_value)` and appends one `("", f"{relation.label} {identifying_value(target_table, record)}")` row per match.
   - Also returns `field_row_index: list[int]`, the row index of each field's own line, so the field-based `selected`/`scroll_offset` indices (unchanged navigation model) can be translated into row indices for `draw_panel`.
3. `TableView.render()` passes the cached rows straight to `draw_panel`, translating `self.selected`/`self.scroll_offset` (both field indices) into row indices via `field_row_index`.

### Key architecture decisions

- **Resolve and cache relation rows once, in `__init__`, not on every `render()` call.** `render()` can be invoked on every keypress; re-running `fetch_by_column_equals` per relation per render would issue unbounded DB queries per frame, directly working against F5/AC6 ("no upper limit... no truncation") which implies the list can be large. Caching mirrors the existing pattern where `self.fields` is already computed once in `__init__` from an immutable `record`. Trade-off: if the underlying data changes while a `TableView` is open, the relation rows go stale until the view is rebuilt (pushed again) — acceptable, since the PRD has no requirement for live refresh and `record` itself is already a point-in-time snapshot.
- **The relation's local column shows the raw local value on its first line, not the existing `RelationField.value` bracket format (`"Company[42]"`).** The PRD's domain concepts section is explicit: "Its own value is always shown as the first line under that column" (§5), and the briefing's worked example shows the bare value (`123456`), not a bracketed form. `RelationField.foreign_key_value` (already computed by `build_fields`) is reused for this — no change to `fields.py` is needed. `RelationField.value` (the bracket format) remains as-is and continues to be used only internally by the pre-existing follow-to-single-match code path in `_follow_selected_field`, so no existing test (`test_ep3_t2_t3_fields.py`) is affected.
- **Continuation rows use an empty-string column name** (`("", "...")`), matching the briefing's example and requiring zero changes to `draw_panel`'s row model (`list[tuple[str, str]]`). This keeps `draw_panel` reusable as-is and avoids inventing a new rendering primitive for a feature the PRD scopes as display-only.
- **`table.relations` iteration order (not a dict) drives grouping**, because the existing `relations_by_local_column` dict comprehension in `fields.py` keeps only the *last* relation per local column, which is insufficient once a column can have more than one relation (F7/AC9). `build_display_rows` iterates `table.relations` directly and filters by `local_column`, so multiple relations sharing one local column are all resolved and appended in configured order, independent of `RelationField`'s single-relation limitation.
- **Enter-to-follow behavior (`_follow_selected_field`) is unchanged.** It still resolves only via `next(r for r in self.table.relations if r.local_column == field.column)` — the first configured relation for that column — regardless of how many relations or related entities are now listed inline. The PRD scopes this epic to display only ("Out of scope: navigating from a listed related entity... unless already supported elsewhere"), so multi-relation columns display all groups but Enter still follows the first relation only. This is an explicit assumption, not a gap this epic closes.

## 4. Data model

No changes to `dbbro/config/models.py` (`Table`, `Relation`, `Config`) — this epic is display-only per the PRD's out-of-scope note. New, purely computed (non-persisted) shapes:

- `field_row_index: list[int]` — row index of each field's primary line within the expanded row list; parallel to `fields`.
- Rows remain `list[tuple[str, str]]` (name, value), identical to `draw_panel`'s existing contract — no new row type is introduced.

## 5. API / interfaces

New module `dbbro/ui/relation_rows.py`:

```python
def identifying_value(table: Table, record: dict[str, Any]) -> str:
    """Concatenates `table.search_columns` values, space-separated, in
    declared order. If `table.search_columns` is empty, falls back to the
    value of `table.columns[0]` (F9/AC10). Assumes (per PRD §10) this is
    never empty in practice."""

def build_display_rows(
    fields: list[Field],
    table: Table,
    config: Config,
    conn,
) -> tuple[list[tuple[str, str]], list[int]]:
    """Expands one row per plain Field, and (own-value row + one row per
    matched related entity per relation, in table.relations order) per
    RelationField. Returns (rows, field_row_index)."""
```

`TableView` changes (`dbbro/ui/table_view.py`):
- `__init__` gains `self.rows, self.field_row_index = build_display_rows(self.fields, table, config, conn)`.
- `render()` changes from `rows = [(field.column, field.value) for field in self.fields]` to using `self.rows`, and passes `highlighted_index=self.field_row_index[self.selected]` and `scroll_offset=self.field_row_index[self.scroll_offset]` to `draw_panel` (both translated from field indices to row indices).
- `handle_key`, `_update_scroll`, `_follow_selected_field` are unchanged — they continue to operate on field indices (`self.fields`), preserving today's per-field Up/Down navigation semantics; only the visual row list underneath grows.

No changes to `draw_panel` (`dbbro/ui/screen.py`), `fetch_by_column_equals` (`dbbro/db/queries.py`), or `build_fields`/`Field`/`RelationField` (`dbbro/ui/fields.py`).

## 6. Implementation plan (TDD)

### T1. `identifying_value` builds a display string from `search_columns`, falling back to the first defined column        (closes: F2, F9, AC2, AC7, AC10)
- Failing tests to write first:
  - `tests/test_ep3b_t1_identifying_value.py::test_identifying_value_concatenates_search_columns_in_order` — `Table(search_columns=("tsId", "name"))`, record with both, asserts the two values appear space-separated in declared order.
  - `test_identifying_value_uses_only_declared_search_columns` — record has extra columns not in `search_columns`; asserts they're excluded.
  - `test_identifying_value_single_search_column_returns_bare_value` — one-column `search_columns`, no separator artifacts.
  - `test_identifying_value_falls_back_to_first_column_when_search_columns_empty` — `Table(search_columns=(), columns=("id", "name"))`, asserts the result equals the record's `"id"` value (`table.columns[0]`), not an empty string.
- Production code to make them pass:
  - `dbbro/ui/relation_rows.py::identifying_value(table, record)` — when `table.search_columns` is empty, use `(table.columns[0],)` as the effective column tuple instead.
- Refactor step:
  - None expected; the fallback is a one-line conditional ahead of the existing concatenation.

### T2. `build_display_rows` expands relation columns into own-value + related-entity rows        (closes: F1, F2, F3, F4, F6, F7, F8, N1, AC1, AC2, AC3, AC8)
- Failing tests to write first:
  - `tests/test_ep3b_t2_build_display_rows.py::test_plain_column_produces_one_row_unchanged` — non-relation `Field` yields `(column, value)` exactly as before.
  - `test_relation_column_first_row_shows_raw_local_value` — `RelationField` yields its own row using `foreign_key_value`, not the bracketed `.value`.
  - `test_relation_column_appends_one_row_per_matched_related_entity` — stub `conn`/`fetch_by_column_equals` (via sqlite fixture from `tests/conftest.py`, seeded with 3 matching Shop rows) returns 3 continuation rows with empty name and `"{label} {identifying_value}"` content.
  - `test_continuation_rows_use_empty_column_name` — asserts row name is `""` for related-entity lines.
  - `test_field_row_index_points_to_each_fields_own_line` — with one relation producing 2 related rows, asserts `field_row_index` correctly skips over them for the next field.
- Production code to make them pass:
  - `dbbro/ui/relation_rows.py::build_display_rows(fields, table, config, conn)`.
  - `dbbro/ui/table_view.py::TableView.__init__` — call `build_display_rows` and store `self.rows`/`self.field_row_index`.
  - `dbbro/ui/table_view.py::TableView.render` — use `self.rows` and translate `self.selected`/`self.scroll_offset` via `self.field_row_index`.
- Refactor step:
  - Extract the per-relation fetch-and-format loop in `build_display_rows` into a small private helper if the function grows past ~20 lines, to keep it independently testable from the column-iteration loop.

### T3. Zero and one related entity render identically to the multi-entity case        (closes: F4, AC4, AC5)
- Failing tests to write first:
  - `tests/test_ep3b_t3_cardinality.py::test_zero_matches_produce_no_continuation_rows` — `fetch_by_column_equals` stub returns `[]`; asserts only the own-value row exists for that column, no extra rows.
  - `test_single_match_produces_exactly_one_continuation_row` — asserts one related-entity row, formatted identically to the multi-match case (same `"{label} {identifying_value}"` shape).
- Production code to make them pass:
  - No new production code beyond T2 — `build_display_rows`'s loop over `related_records` already naturally handles 0/1/N; this task is verification, not new logic.
- Refactor step:
  - None.

### T4. Table view renders an unbounded number of related-entity rows without truncation        (closes: F5, AC6)
- Failing tests to write first:
  - `tests/test_ep3b_t4_no_cap.py::test_build_display_rows_emits_a_row_per_match_with_no_cap` — seed 500 matching related records via the sqlite fixture; asserts `len(rows)` reflects all 500 continuation rows (no slicing/truncation inside `build_display_rows`).
  - `test_table_view_scroll_reaches_rows_beyond_visible_height` — construct a `TableView` with 500 related rows and a small `visible_height`; drive `handle_key(keys.DOWN)` repeatedly and assert `scroll_offset` (translated to row index) eventually exposes rows near the end, i.e. `draw_panel`'s own existing scroll windowing (`rows[scroll_offset:scroll_offset+visible_height]`) is what bounds what's on screen, not `build_display_rows`.
- Production code to make them pass:
  - None beyond T2 (this is an anti-truncation guard against accidentally adding a cap/slice in `build_display_rows`).
- Refactor step:
  - None.

### T5. Two configured relations on the same local column are grouped and ordered        (closes: F7, AC9)
- Failing tests to write first:
  - `tests/test_ep3b_t5_multi_relation_grouping.py::test_two_relations_on_same_local_column_both_produce_rows` — `Table` with two `Relation`s sharing `local_column="id"` (e.g. `Shop` and `Order`), each with its own matches; asserts both relations' related rows are present.
  - `test_relation_groups_appear_in_table_relations_order` — asserts the first configured relation's rows all precede the second configured relation's rows, regardless of dict/hash ordering.
  - `test_relations_by_local_column_dict_limitation_does_not_drop_a_relation` — regression test proving `build_display_rows` does not rely on `fields.py`'s `relations_by_local_column` (which keeps only the last relation per column); asserts both relations still resolve even though `RelationField.related_table`/`foreign_key_value` reflect only one of them.
- Production code to make them pass:
  - `dbbro/ui/relation_rows.py::build_display_rows` — confirm/adjust the relation-filtering loop (`for relation in table.relations: if relation.local_column != field.column: continue`) iterates the full tuple, not a per-column dict.
- Refactor step:
  - None expected; this task mainly guards T2's design choice with a dedicated regression test.

## 7. Non-functional concerns

- **Performance (N1, and the PRD's own noted gap on very large in-table lists):** related rows are resolved once per `TableView` construction (§3 decision), not per render/keypress, bounding DB round-trips to one `fetch_by_column_equals` call per relation per view. Actual on-screen rendering is already bounded by `draw_panel`'s existing `rows[scroll_offset:scroll_offset+visible_height]` windowing (`dbbro/ui/screen.py`), so a large related-entity list affects memory (holding all rows in `self.rows`) but not per-frame rendering cost.
- **Consistency:** the row-expansion logic is table/relation-agnostic (F8) — it operates uniformly off `table.relations` and `field.column`, with no special-casing per table name.
- **No new I/O paths:** reuses the existing `fetch_by_column_equals` query function and connection object; no new SQL is introduced.

## 8. Risks & mitigations

- Risk: a foreign table used as a relation target has an empty `search_columns` (e.g. the briefing's own `Shop` example config doesn't declare one), which would make `identifying_value` return `""`, contradicting the PRD's assumption that it's never empty. Mitigation: closed by F9/AC10 — `identifying_value` falls back to `table.columns[0]` when `search_columns` is empty, guaranteeing a non-empty result as long as `table.columns` itself is non-empty (a pre-existing config invariant this epic does not need to (re-)validate).
- Risk: caching `self.rows` in `__init__` means a `TableView` never reflects underlying data changes made after it was constructed. Mitigation: consistent with existing behavior (`self.record`/`self.fields` are already point-in-time), no regression introduced.
- Risk: translating field indices to row indices (`field_row_index`) is new bookkeeping that could silently desync if `build_display_rows`' iteration order diverges from `build_fields`' iteration order. Mitigation: T2's dedicated `field_row_index` test and T5's ordering regression test guard this directly.

## 9. Open architecture decisions

None. The PRD (~91% confidence, all FR/NFR/AC resolved) leaves no ambiguity that rises to a high-impact, user-facing architecture choice — the only implementation gaps (identifying-value separator, own-value line format, grouping mechanism, caching point) are resolved above with concrete rationale grounded directly in the PRD's domain concepts, worked example, and out-of-scope notes, and each is a low-risk, easily-revisited internal detail rather than a decision that changes product behavior.
