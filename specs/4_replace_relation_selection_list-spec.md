# Epic 4 — Replace Relation Selection List — Technical Specification

Tech spec for `specs/4_replace_relation_selection_list.md`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~94% after revision 1 — every FR/NFR/AC is covered by a §6 task, §3's architecture is concrete enough to start T1 without further design, and D1 (the only architecturally ambiguous point) is resolved via an architecture-advisor consultation with no open decisions remaining; the small residual risk is that T5–T7 rely on correctly editing three pre-existing tests (`test_ep3_t6_t8_navigation.py`, `test_ep2_t3_view_help_keys.py`) rather than adding wholly new coverage, so a slip there could silently narrow regression coverage instead of failing loudly

## 1. Overview

Epic 3 made every related entity for a configured relation visible as its own row beneath the relation's local column, but `TableView` still navigated and opened rows at *field* granularity (one `selected` index per `Field`/`RelationField`, translated to a row index only for rendering) and still routed Enter through the old `SelectionList` modal whenever a relation had more than one match. This epic switches `TableView`'s navigation model to row granularity — so every related-entity row is independently selectable and independently openable via Enter — and retires the `SelectionList`-based follow flow entirely, per `specs/4_replace_relation_selection_list.md`.

Scope boundary: only `dbbro/ui/table_view.py` and `dbbro/ui/relation_rows.py` change. `SelectionList` itself (`dbbro/ui/selection_list.py`) is untouched and remains in use by the unrelated search flow (`dbbro/ui/search_prompt.py`); this epic only stops `TableView` from constructing one.

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| F1 | Up/Down reaches every row, including related-entity rows | §3, §6 T2 |
| F2 | Enter on a related-entity row opens that entity directly | §3, §6 T1, T3 |
| F3 | Enter on a local column row with >1 match does nothing | §3, §6 T1, T4 |
| F4 | Enter on a local column row with exactly 1 match opens it directly | §3, §6 T1, T3 |
| F5 | Selection list is never opened from the relation-follow flow | §3, §6 T3, T7 |
| F6 | Zero-match relations have no related-entity row to open | §3, §6 T1, T5 |
| N1 | Opening a related entity requires no intermediate screen | §3, §6 T3, T8 |
| N2 | Help bar's "enter open" reflects whether Enter would act | §3, §6 T6 |
| AC1 | Enter on a related-entity row opens that entity | §6 T3 |
| AC2 | Enter on a local column row with >1 match does nothing | §6 T4 |
| AC3 | Enter on a local column row with exactly 1 match opens it | §6 T3 |
| AC4 | No selection list is shown at any point | §6 T3, T7 |
| AC5 | Zero-match relation has nothing to navigate to or open | §6 T5 |
| AC6 | Help bar shows "enter open" for related-entity row or 1-match local column | §6 T6 |
| AC7 | Help bar omits "enter open" for a >1-match local column | §6 T6 |
| AC8 | Breadcrumb/history behave identically to the existing push flow | §6 T8 |

## 3. Architecture

### Components touched

- `dbbro/ui/relation_rows.py` — `build_display_rows` changes its second return value from `field_row_index: list[int]` to `row_targets: list[RowTarget]`, a per-row navigation-target array parallel to `rows`. New dataclasses `LocalColumnTarget` and `RelatedEntityTarget` (the `RowTarget` union) are added here.
- `dbbro/ui/table_view.py` (`TableView`) — `self.selected`/`self.scroll_offset` become row indices directly (no more field→row translation); `handle_key`/`_update_scroll` iterate `len(self.rows)` instead of `len(self.fields)`; `_follow_selected_field` is replaced by `_open_selected_row`, which dispatches on `self.row_targets[self.selected]` instead of re-running `fetch_by_column_equals` or constructing a `SelectionList`.
- `dbbro/ui/fields.py`, `dbbro/ui/screen.py`, `dbbro/ui/selection_list.py`, `dbbro/ui/errors.py` — unchanged. `build_fields` still produces the field list `build_display_rows` iterates; `draw_panel` already renders an arbitrary row list and needs no change since rows stay `list[tuple[str, str]]`; `SelectionList` remains for the unrelated search flow; `RelationLookupFailedError` remains defined (still raised/tested elsewhere for search) but is no longer raised by `TableView`.

### Data flow

1. `TableView.__init__` builds `self.fields = build_fields(table, record)` as before, then `self.rows, self.row_targets = build_display_rows(self.fields, table, config, conn)`.
2. `build_display_rows`, for each `RelationField`, resolves matches once per configured relation on that column (as it already does in Epic 3), and additionally records, per row:
   - the local column's own row → `LocalColumnTarget(target_table=<first configured relation's target_table>, matches=<that first relation's matches>)` (see D1).
   - each related-entity row → `RelatedEntityTarget(target_table=<that row's relation's target_table>, record=<the matched row>)`.
   - a plain (non-relation) field's row → `None`.
3. `TableView.selected` and `TableView.scroll_offset` now index directly into `self.rows`/`self.row_targets`; `handle_key(DOWN/UP)` wraps modulo `len(self.rows)`, and `_update_scroll` clamps `scroll_offset` against `visible_height` using row indices only — no translation step remains.
4. `render()` passes `self.selected`/`self.scroll_offset` straight through to `draw_panel`.
5. `handle_key(RETURN)` calls `_open_selected_row()`, which inspects `self.row_targets[self.selected]`:
   - `RelatedEntityTarget` → always pushes `self._build_table_view(config.tables[target.target_table], target.record)`.
   - `LocalColumnTarget` with `len(target.matches) == 1` → pushes `self._build_table_view(config.tables[target.target_table], target.matches[0])`.
   - `LocalColumnTarget` with 0 or ≥2 matches, or `None` → returns `None` (no-op), matching F3/F4/F6.

### Key architecture decisions

- **Row-based navigation replaces field-based navigation with a translation layer.** Epic 3 kept `selected`/`scroll_offset` as field indices and translated them to row indices only at render time (`field_row_index`), because at the time no individual related-entity row needed to be independently selectable. Epic 4's entire purpose is making those rows independently selectable, so the translation layer is now solving the wrong problem — removing it and operating `selected`/`scroll_offset` directly as row indices makes `TableView`'s navigation model match `draw_panel`'s existing row model 1:1, with no index-space conversion left anywhere.
- **Relation matches are resolved once in `__init__` and carried per-row via `row_targets`; `_open_selected_row` never touches `conn` or re-fetches.** This was already Epic 3's caching strategy for *display*; Epic 4 extends it to *navigation* as well. It's what makes the zero-match and multi-match no-op cases (F3/F6) simple and safe — there is no lookup left to fail, so `RelationLookupFailedError` is never raised from this path (a deliberate behavior change from the pre-Epic-4 code, which used to raise it on a zero-match Enter).
- **`LocalColumnTarget` on a multi-relation column reflects only the first configured relation (D1, resolved).** When a local column has more than one `Relation` (e.g. "has Shop" and "has Order" sharing `id`), the local-column-row shortcut's one-match check applies only to `table.relations`'s first entry for that column — the same relation the pre-Epic-4 `_follow_selected_field` already picked via `next(r for r in table.relations if r.local_column == field.column)`. Every relation's related-entity rows (first or not) remain independently reachable via their own rows regardless, so this only affects the shortcut's convenience behavior, never coverage. *(Architecture advisor: Epic 4's per-row navigation already gives every relation full independent reachability, making the shortcut's behavior on multi-relation columns a non-functional convenience detail rather than a coverage gap, so preserving the exact pre-existing selection precedent is lowest-risk.)*
- **Help-bar "enter open" visibility is computed from `row_targets[self.selected]`, not from `isinstance(field, RelationField)`.** Epic 3's `help_keys` only checked whether the highlighted field was a `RelationField` at all; Epic 4 tightens this to reflect whether Enter would actually do something for the *current row* — true for any `RelatedEntityTarget`, and for a `LocalColumnTarget` only when it has exactly one match — closing N2/AC6/AC7.

## 4. Data model

New, purely computed (non-persisted) shapes in `dbbro/ui/relation_rows.py`:

```python
@dataclass(frozen=True)
class LocalColumnTarget:
    target_table: str
    matches: tuple[dict[str, Any], ...]

@dataclass(frozen=True)
class RelatedEntityTarget:
    target_table: str
    record: dict[str, Any]

RowTarget = LocalColumnTarget | RelatedEntityTarget | None
```

`rows: list[tuple[str, str]]` is unchanged from Epic 3. `row_targets: list[RowTarget]` replaces `field_row_index: list[int]` as `build_display_rows`'s second return value, parallel to `rows` (one entry per row, not per field).

## 5. API / interfaces

`dbbro/ui/relation_rows.py`:

```python
def build_display_rows(
    fields: list[Field],
    table: Table,
    config: Config,
    conn,
) -> tuple[list[tuple[str, str]], list[RowTarget]]:
    """Expands one row per plain Field (target None), and (local-column
    row + one row per matched related entity per relation, in
    table.relations order) per RelationField. The local-column row's
    target reflects only the first configured relation for that column
    (D1); each related-entity row's target reflects its own relation and
    matched record."""
```

`dbbro/ui/table_view.py` (`TableView`):
- `__init__` gains `self.row_targets` (alongside the now row-indexed `self.rows`); drops `self.field_row_index`.
- `render()` passes `highlighted_index=self.selected`, `scroll_offset=self.scroll_offset` directly (no translation).
- `handle_key` — `DOWN`/`UP` branches now compute modulo `len(self.rows)`.
- `help_keys()` — replaces the `isinstance(self.fields[self.selected], RelationField)` check with a new private `_is_openable(self.row_targets[self.selected]) -> bool` helper.
- `_follow_selected_field` is renamed `_open_selected_row` and no longer imports/uses `fetch_by_column_equals`, `SelectionList`, or `RelationLookupFailedError`.

No changes to `draw_panel` (`dbbro/ui/screen.py`), `fetch_by_column_equals` (`dbbro/db/queries.py`), `build_fields`/`Field`/`RelationField` (`dbbro/ui/fields.py`), or `SelectionList` (`dbbro/ui/selection_list.py`).

## 6. Implementation plan (TDD)

### T1. `build_display_rows` returns per-row `RowTarget`s instead of `field_row_index`        (closes: F2, F3, F4, F6, AC1, AC3, AC5)
- Failing tests to write first:
  - `tests/test_ep4_t1_row_targets.py::test_plain_field_row_has_no_target` — a non-relation `Field`'s row has `row_targets[i] is None`.
  - `test_local_column_row_target_holds_first_relations_matches` — single-relation column with 2 matches: `LocalColumnTarget(target_table="Shop", matches=(<2 dicts>,))` at the local column's row index.
  - `test_related_entity_row_target_holds_its_own_record` — each continuation row's target is `RelatedEntityTarget(target_table=..., record=<that exact matched dict>)`.
  - `test_zero_match_relation_produces_local_column_target_with_empty_matches` — 0 matches: no continuation rows, but `LocalColumnTarget(matches=())` still present at the local column's row.
  - `test_multi_relation_local_column_target_reflects_first_configured_relation_only` — column with two relations (e.g. "has Shop" then "has Order"): `LocalColumnTarget.target_table` and `.matches` come from the *first* (`Shop`), not the second, regardless of match counts on either (D1).
- Production code to make them pass:
  - `dbbro/ui/relation_rows.py` — add `LocalColumnTarget`/`RelatedEntityTarget` dataclasses and `RowTarget` alias; rewrite `build_display_rows` to build and return `row_targets` alongside `rows`.
- Refactor step:
  - Remove the old `field_row_index`-building logic entirely; no dual-return-shape transition period.

### T2. `TableView` navigates rows directly, not fields        (closes: F1)
- Failing tests to write first:
  - `tests/test_ep4_t2_row_navigation.py::test_down_moves_through_every_row_including_continuation_rows` — a relation with 3 matches: pressing `DOWN` repeatedly visits the local column row, then each of the 3 continuation rows individually (`selected` takes 4 distinct values across the group, not 1).
  - `test_up_down_wraps_across_full_row_count` — wrapping uses `len(self.rows)`, not `len(self.fields)`.
  - `test_scroll_offset_tracks_selected_row_directly` — with a small `visible_height` and enough continuation rows to force scrolling, `scroll_offset` advances in row units with no remaining translation step.
- Production code to make them pass:
  - `dbbro/ui/table_view.py::TableView.__init__` — store `self.rows, self.row_targets = build_display_rows(...)`; drop `self.field_row_index`.
  - `handle_key`'s `DOWN`/`UP` branches and `_update_scroll` — operate on `len(self.rows)` instead of `len(self.fields)`.
  - `render()` — pass `self.selected`/`self.scroll_offset` to `draw_panel` directly.
- Refactor step:
  - Confirm `tests/test_ep3_t4_t5_selection_scroll.py` (a relation-free table, where row count equals field count) still passes unchanged — it exercises the same navigation code path with no continuation rows, so it's a free regression check, not a test to rewrite.

### T3. Enter opens the highlighted row's target directly; the selection-list follow-flow is retired        (closes: F2, F4, F5, N1, AC1, AC3, AC4)
- Failing tests to write first:
  - `tests/test_ep4_t3_open_row.py::test_enter_on_related_entity_row_pushes_that_records_table_view` — highlight a continuation row, press Enter, assert the pushed `TableView`'s `record` is exactly that row's matched record.
  - `test_enter_on_related_entity_row_never_shows_a_selection_list` — assert the returned `Transition.view` is a `TableView`, never a `SelectionList`.
  - `test_enter_on_local_column_with_exactly_one_match_opens_directly` — single-match relation, highlight the local column row, press Enter, assert it pushes that one match's `TableView` directly (same outcome as pre-Epic-4 behavior, now driven by `row_targets` instead of a live `fetch_by_column_equals` call).
  - `test_enter_on_non_relation_row_does_nothing` — plain field row, Enter returns `None`.
- Production code to make them pass:
  - `dbbro/ui/table_view.py` — replace `_follow_selected_field` with `_open_selected_row`, dispatching on `self.row_targets[self.selected]` per §3's data flow; remove the `fetch_by_column_equals`, `SelectionList`, and `RelationLookupFailedError` imports/usages from this file.
- Refactor step:
  - `_build_table_view` is unchanged and reused as-is by `_open_selected_row` for both target types.

### T4. Enter on a local column row with more than one match does nothing        (closes: F3, AC2)
- Failing tests to write first:
  - `tests/test_ep4_t4_local_column_multi_match.py::test_enter_on_local_column_with_multiple_matches_returns_none` — 3-match relation, highlight the local column row, press Enter, assert `None`.
  - `test_enter_on_local_column_with_multiple_matches_does_not_change_view` — assert `self.selected`/`self.rows` are unchanged after the no-op Enter.
- Production code to make them pass:
  - None beyond T3 — `_open_selected_row`'s `len(target.matches) == 1` guard already covers this; this task verifies it.
- Refactor step:
  - None.

### T5. Zero-match relations have nothing to navigate to or open        (closes: F6, AC5)
- Failing tests to write first:
  - `tests/test_ep4_t5_zero_matches.py::test_enter_on_local_column_with_zero_matches_returns_none_not_raises` — 0-match relation, highlight the local column row, press Enter, assert `None` is returned and no exception is raised.
- Production code to make them pass:
  - None beyond T3 — `LocalColumnTarget(matches=())` falls through the `== 1` check to the no-op branch.
- Refactor step:
  - Update `tests/test_ep3_t6_t8_navigation.py::test_return_on_relation_field_with_zero_matches_raises_relation_lookup_failed`: rename it to reflect the new no-op behavior and change its assertion from `pytest.raises(RelationLookupFailedError)` to `assert view.handle_key(keys.RETURN) is None`, since this epic deliberately changes that behavior (PRD Cycle 1, Q4).

### T6. Help bar's "enter open" reflects whether Enter would act on the current row        (closes: N2, AC6, AC7)
- Failing tests to write first:
  - `tests/test_ep4_t6_help_bar.py::test_help_shows_enter_open_for_related_entity_row` — highlight a continuation row, assert `("enter", "open")` is present.
  - `test_help_shows_enter_open_for_single_match_local_column_row` — highlight a 1-match local column row, assert present.
  - `test_help_omits_enter_open_for_multi_match_local_column_row` — highlight a 3-match local column row, assert absent.
  - `test_help_omits_enter_open_for_zero_match_local_column_row` — highlight a 0-match local column row, assert absent.
  - `test_help_omits_enter_open_for_plain_field_row` — unchanged from Epic 3, still absent.
- Production code to make them pass:
  - `dbbro/ui/table_view.py::TableView.help_keys` — replace the `isinstance(..., RelationField)` check with `self._is_openable(self.row_targets[self.selected])`, implemented as: `True` for `RelatedEntityTarget`; `len(matches) == 1` for `LocalColumnTarget`; `False` for `None`.
- Refactor step:
  - Update `tests/test_ep2_t3_view_help_keys.py::test_table_view_includes_open_when_relation_field_selected`: it currently asserts `("enter", "open")` appears for a `RelationField` with zero seeded matches, which was valid under Epic 3's looser check but contradicts this task's stricter one — seed exactly one matching `Shop` row in that test's sqlite fixture so the assertion continues to hold under the new semantics.

### T7. The relation-follow flow never constructs a `SelectionList`        (closes: F5, AC4)
- Failing tests to write first:
  - none new — this task replaces existing tests rather than adding coverage.
- Production code to make them pass:
  - None beyond T3.
- Refactor step:
  - In `tests/test_ep3_t6_t8_navigation.py`, replace `test_return_on_relation_field_with_multiple_matches_opens_selection_list` and `test_choosing_from_selection_list_displays_new_table_view_per_t6` with `test_enter_on_local_column_with_multiple_matches_does_not_open_selection_list` (asserts `handle_key(RETURN)` returns `None`, per T4) and `test_enter_on_a_specific_related_entity_row_opens_it_directly` (navigate `DOWN` onto the desired continuation row, press Enter, assert the pushed view is a `TableView` for that exact match — never a `SelectionList`), so this file's coverage moves from the retired flow to the new one instead of asserting dead behavior.

### T8. Breadcrumb and history behave identically whether opening a related-entity row or (previously) the local column's single match        (closes: N1, AC8)
- Failing tests to write first:
  - `tests/test_ep4_t8_breadcrumb_history.py::test_opening_related_entity_row_extends_breadcrumb_like_existing_flow` — open a continuation row, assert the breadcrumb's last stop matches the opened record's table/primary key, exactly as `tests/test_ep3_t6_t8_navigation.py::test_return_on_relation_field_with_one_match_extends_breadcrumb` already asserts for the single-match case.
  - `test_opening_related_entity_row_records_history_entry_like_existing_flow` — with a `history` object passed to `TableView`, assert `history.add_entry` was called with the new view, exactly as the existing single-match/selection-list flow already does via `_build_table_view`.
- Production code to make them pass:
  - None beyond T3 — `_build_table_view` (unchanged) already pushes the breadcrumb stop and records history for every caller.
- Refactor step:
  - None.

## 7. Non-functional concerns

- **Consistency (N2):** `_is_openable` is the single source of truth for "would Enter do something on this row," shared by `help_keys` (T6) and implicitly mirrored by `_open_selected_row`'s dispatch (T3/T4/T5) — both read the same `row_targets` structure, so there is no risk of the help bar and actual Enter behavior disagreeing.
- **No new I/O paths:** relation matches are still fetched exactly once per relation per `TableView` construction (Epic 3's existing behavior, §3); this epic adds no new database calls — if anything, it removes the one `fetch_by_column_equals` call that used to happen at Enter time in `_follow_selected_field`.
- **Behavior change explicitly scoped:** the zero-match case no longer raises `RelationLookupFailedError` from `TableView` (T5); `RelationLookupFailedError` itself is untouched and remains raised/tested for the unrelated search flow, so this is a narrowing of one call site's behavior, not a removal of the exception type.

## 8. Risks & mitigations

- Risk: removing `field_row_index` and switching `selected`/`scroll_offset` to row indices could silently break any other code path still assuming field-level indexing. Mitigation: `tests/test_ep3_t4_t5_selection_scroll.py` (relation-free table) exercises the same navigation code with row count equal to field count, giving a zero-relation regression check "for free"; T2 explicitly re-runs it rather than rewriting it.
- Risk: `tests/test_ep2_t3_view_help_keys.py`'s existing relation-field help-bar test relied on Epic 3's looser `isinstance` check and will fail once T6 lands, since it seeds zero matches. Mitigation: T6's refactor step updates that fixture to seed exactly one match, keeping its original intent (a `RelationField` shows "enter open") valid under the new, stricter rule.
- Risk: `tests/test_ep3_t6_t8_navigation.py` asserts three behaviors this epic deliberately changes (zero-match raises, multi-match opens a `SelectionList`, choosing from that list opens a `TableView`). Mitigation: T5 and T7 replace those three tests in place rather than leaving them to fail silently — each replacement is named explicitly in this plan so no coverage is dropped, only relocated to match the new behavior.

## 9. Open architecture decisions

None. D1 (which relation a multi-relation local column's shortcut targets) was resolved in this revision via the architecture-advisor consultation in §3 — the shortcut targets only the first configured relation for that column, matching the exact pre-Epic-4 precedent, since per-row navigation already gives every relation independent reachability regardless.
