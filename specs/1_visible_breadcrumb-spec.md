# Epic 1 — Visible Breadcrumb — Technical Specification

Tech spec for [`1_visible_breadcrumb.md`](./1_visible_breadcrumb.md). Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~95% after revision 3 — root cause confirmed by direct code reading and D1 resolved (mutually exclusive root/current display), now fully folded into §10's decision log with no dangling open-decision text left in the body; remaining minor risk is the two cross-epic `render_frame` signature changes (this epic's `breadcrumb` param, the sibling epic's `history` param) still need to be composed by whoever implements the second one

## 1. Overview

The breadcrumb (`dbbro/navigation/breadcrumb.py`) already tracks navigation state correctly — it is pushed to on every relation drill-down and reset on every fresh search — but nothing in `dbbro/ui/` ever draws it to the screen. This epic adds that missing render path: a one-line breadcrumb pinned to the terminal's top row, with a blank separator row beneath it, showing either a root label (before any record is open) or the current table and record. Scope is `dbbro/ui/` (a new `breadcrumb_bar.py` module, a `screen.py` addition, and a `render_frame`/`run()` wiring change in `app.py`). See PRD: [`specs/1_visible_breadcrumb.md`](./1_visible_breadcrumb.md).

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| F1 / AC1 | Breadcrumb shown at top of every screen with a navigation location | §3, §6 T2, T3 |
| F2 / AC5 | Reflects only current table/record, omitting intermediate hops | §4, §6 T1 |
| F3 / AC3 | Updates whenever the user navigates to a different screen | §3, §6 T3 (recomputed every `render_frame` call) |
| F4 / AC6 | Root segment shown at the very top of the hierarchy | §4, §6 T1 |
| F5 / AC7 | Truncates middle, keeps first and last visible, on overflow | §4, §6 T1 |
| F6 / AC8 | Record segment identified by primary key value | §4 (already `BreadcrumbStop.primary_key_value`), §6 T1 |
| F7 / AC10 | Visible during loading/error states | §3, §6 T3 (modal render path) |
| N1 / AC2 | Legible: not blank, not styled invisibly, not obscured | §3 (Key architecture decision), §6 T2 |
| N2 / AC4 | Remains visible regardless of terminal size | §3, §6 T2 |
| N3 / AC9 | Separated from the screen body by a blank line | §3 (Key architecture decision), §6 T2 |

## 3. Architecture

### Components

- **`render_breadcrumb_line(stops: list[BreadcrumbStop], width: int) -> str`** (new, `dbbro/ui/breadcrumb_bar.py`) — pure function: returns `TOP_LEVEL_LABEL` ("Tables") if `stops` is empty (F4/AC6); otherwise formats `stops[-1]` (the current table/record, ignoring any earlier stops per F2/AC5) as `"{table} > {primary_key_value}"`; fits the result to `width`, truncating the middle and keeping head/tail characters visible if it doesn't fit (F5/AC7).
- **`draw_breadcrumb_bar(screen, stops: list[BreadcrumbStop]) -> None`** (new, `dbbro/ui/screen.py`, alongside `draw_panel`/`draw_modal`) — reads `max_height, max_width = screen.getmaxyx()`, calls `render_breadcrumb_line(stops, max_width)`, and writes it at row `0`. Row `1` is left untouched (already blanked by the per-frame `stdscr.erase()` in `render_frame`), satisfying N3/AC9 without any extra drawing call.
- **Top-row reservation in `draw_panel`/`draw_modal`** — both functions already derive their layout from a single `getmaxyx()` call at the top (`screen.py:48,78`). They are changed to treat the first `TOP_RESERVED_ROWS = 2` rows (breadcrumb + blank separator) as unusable: `draw_panel`'s `visible_height = max(1, max_height - 4 - TOP_RESERVED_ROWS)`, and both functions' centering (`_center_origin`) is changed to clamp its minimum `start_y` to `TOP_RESERVED_ROWS` instead of `0`.

### Data flow

`render_frame` (`app.py:67-77`) currently does `erase → view.render(screen) → optional modal.render(screen)`. It changes to: `erase → draw_breadcrumb_bar(screen, breadcrumb.as_list()) → view.render(screen) → optional modal.render(screen)`. Drawing the breadcrumb first, immediately after `erase`, means it is always present regardless of whatever the view or a pending modal does afterward, and can never be overwritten. `render_frame` gains a `breadcrumb: Breadcrumb` parameter (mirroring how the PRD's sibling epic — Navigation Key Help — separately proposes adding a `history` parameter to the same function; both additions are independent and compose without conflict, since each reads its own state and writes to a different screen row).

### Key architecture decisions

- **Reserve the top two rows by shrinking usable height and clamping the minimum start row, not by drawing over unclamped content.** This mirrors the exact pattern `draw_panel`/`draw_modal` already use for their own layout math (a single `getmaxyx()`-derived height feeding every clamp), so adding a second reserved region (top, in addition to any future bottom reservation) is a minimal, consistent extension rather than a new layout mechanism. Rejected alternatives: drawing the breadcrumb over whatever the view already rendered (risks the view's own top border overwriting it, since draw order would then matter and is fragile), and using `curses.derwin` subwindows (unused anywhere else in this hand-rolled renderer, would introduce a second layout model).
- **The blank separator row is implicit, not drawn.** `render_frame` already calls `stdscr.erase()` once per frame before any drawing; row 1 satisfies N3 by simply never being written to, avoiding a redundant `addstr(1, 0, " " * width)` call that would only duplicate what `erase()` already guarantees.
- **No caching of the breadcrumb line.** `render_frame` runs on every keypress/resize already; recomputing `render_breadcrumb_line` fresh each call is O(1) and trivially satisfies F3/AC3 without invalidation logic — the same reasoning the sibling Navigation Key Help epic applies to its own help line.

## 4. Data model

- **`BreadcrumbStop`** (existing, `dbbro/navigation/breadcrumb.py`, unchanged) — `table: str`, `primary_key_value: str`. No new fields needed: F6/AC8 ("record segment identified by primary key value") is already exactly what this dataclass stores.
- **`Breadcrumb`** (existing, unchanged) — `push`, `reset`, `as_list()`. This epic only adds a *reader* of `as_list()`; it does not change how or when stops are pushed or reset (that logic, in `table_view.py` and `search_prompt.py`, is out of scope per the PRD's "no dependency on other epics" and "not about incorrect hierarchy data" assumption).
- **`TOP_LEVEL_LABEL = "Tables"`** (new, `dbbro/ui/breadcrumb_bar.py`) — the root segment shown when `Breadcrumb.as_list()` is empty, i.e. whenever the current view is `SearchSelectionDialog`, `SearchValuePrompt`, or a `SelectionList` awaiting the user's pick, before any table/record view has been built.
- **Only the last stop is ever rendered.** Even though `Breadcrumb` can accumulate multiple stops while drilling through several relations without an intervening reset, `render_breadcrumb_line` reads only `stops[-1]` — per the PRD's F2/AC5 decision, intermediate relation hops are omitted from the displayed breadcrumb, though the full stack remains available in `Breadcrumb` for any other consumer.

## 5. API / interfaces

```python
# dbbro/ui/breadcrumb_bar.py
TOP_LEVEL_LABEL: str

def render_breadcrumb_line(stops: list[BreadcrumbStop], width: int) -> str: ...

# dbbro/ui/screen.py
def draw_breadcrumb_bar(screen, stops: list[BreadcrumbStop]) -> None: ...
# draw_panel(...) and draw_modal(...) signatures unchanged; internal layout math
# now reserves TOP_RESERVED_ROWS = 2 at the top of the terminal.

# dbbro/ui/app.py
def render_frame(
    stdscr, stack: ViewStack, pending_modal, breadcrumb: Breadcrumb
) -> None: ...
    # signature grows a `breadcrumb` param so it can call draw_breadcrumb_bar()
```

## 6. Implementation plan (TDD)

### T1. `render_breadcrumb_line` — root label, current-only, truncation   (closes: F2, F4, F5, F6, AC5, AC6, AC7, AC8)
- Failing tests to write first:
  - `tests/test_ep1b_t1_render_breadcrumb_line.py::test_empty_stops_returns_root_label` — `render_breadcrumb_line([], 80) == "Tables"`.
  - `test_single_stop_formats_table_and_primary_key` — one `BreadcrumbStop(table="Shop", primary_key_value="543334")` → `"Shop > 543334"`.
  - `test_multiple_stops_shows_only_last_omitting_earlier_hops` — push two stops, assert only the second's table/pk appear, the first's do not.
  - `test_truncates_long_line_keeping_head_and_tail` — a stop whose formatted line exceeds a narrow `width` is truncated with an ellipsis in the middle, and both the first and last few characters of the original text remain present in the result.
  - `test_zero_width_returns_empty_string`.
- Production code to make them pass:
  - `dbbro/ui/breadcrumb_bar.py`: `TOP_LEVEL_LABEL`, `render_breadcrumb_line(stops, width)`.
- Refactor step:
  - Extract the head/tail-truncation arithmetic into a small private helper if `render_breadcrumb_line` grows past ~10 lines.

### T2. `draw_breadcrumb_bar` + top-row reservation in `screen.py`   (closes: F1, N1, N2, N3, AC1, AC2, AC4, AC9)
- Failing tests to write first:
  - `tests/test_ep1b_t2_draw_breadcrumb_bar.py::test_writes_breadcrumb_line_at_row_zero` — using the existing `StubScreen` double, assert an `addstr` call was made with `y == 0`.
  - `test_draw_panel_reserves_top_two_rows` — assert `draw_panel`'s first content row is now at least `TOP_RESERVED_ROWS` (i.e. `start_y >= 2`), never writing to rows `0` or `1`.
  - `test_draw_modal_reserves_top_two_rows` — same assertion for `draw_modal`.
  - `test_breadcrumb_bar_renders_without_crashing_on_small_terminal` — a `StubScreen(height=3, width=20)` still produces a row-0 `addstr` call (AC4).
- Production code to make them pass:
  - `dbbro/ui/screen.py`: add `draw_breadcrumb_bar(screen, stops)`; add `TOP_RESERVED_ROWS = 2`; change `draw_panel`/`draw_modal`'s internal height math and `_center_origin`'s minimum clamp to respect it.
- Refactor step:
  - If `TOP_RESERVED_ROWS` ends up referenced in three or more places with slightly different arithmetic, factor a tiny shared `_usable_top(screen)` helper analogous to how bottom-row reservation is handled in the sibling Navigation Key Help epic, so the two reservations stay easy to compose.

### T3. Wire `draw_breadcrumb_bar` into `render_frame`   (closes: F1, F3, F7, AC1, AC3, AC10)
- Failing tests to write first:
  - `tests/test_ep1b_t3_render_frame_breadcrumb.py::test_breadcrumb_shows_root_label_before_any_search` — run `ui_app.run(StubScreen(...), config, conn=None)` and assert row 0 contains `"Tables"`.
  - `test_breadcrumb_updates_after_drilling_into_relation` — follow a relation into a related `TableView` and assert row 0's content changes to the related table/record.
  - `test_breadcrumb_visible_during_pending_error_modal` — trigger `OperationFailedError`, assert row 0 still shows the current table/record, unaffected by the modal.
  - `test_breadcrumb_visible_during_quit_confirmation` — open the quit modal, assert row 0 is unchanged and still present.
  - `test_breadcrumb_reflects_new_search_after_reset` — perform a fresh search (`s`) after already being deep in a table view, assert row 0 shows only the new result's table/record, not the discarded prior path.
- Production code to make them pass:
  - `dbbro/ui/app.py`: update `render_frame` to accept `breadcrumb` and call `draw_breadcrumb_bar(stdscr, breadcrumb.as_list())` immediately after `stdscr.erase()`; update the two call sites in `run()` (initial render + main loop) to pass `breadcrumb` (already constructed at `app.py:102`).
- Refactor step:
  - Update `render_frame`'s docstring (currently describes only erase/view/modal) to mention the breadcrumb draw, keeping doc and code in sync.

## 7. Non-functional concerns

- **Legibility (N1/AC2):** the breadcrumb line is always non-empty (`TOP_LEVEL_LABEL` as the floor) and drawn with the terminal's default attributes (no reverse-video or color styling applied), so it is never rendered invisibly; drawing it first, immediately after `erase()` and before any view or modal, means nothing else in the frame can obscure it.
- **Robustness to terminal size (N2/AC4):** `render_breadcrumb_line` always fits its output to the current `max_width` (truncating rather than raising), and `draw_breadcrumb_bar` writes unconditionally at row 0 regardless of `max_height`, so even a pathologically small terminal still shows a (possibly heavily truncated) breadcrumb rather than crashing or disappearing.
- **Separation (N3/AC9):** achieved for free by the existing per-frame `erase()` plus never writing to row 1 — no additional rendering cost.
- **Performance:** `render_breadcrumb_line` is O(1) relative to the number of stops (it only ever reads the last one) and O(width) for the truncation fit; negligible relative to existing per-frame `draw_panel`/`draw_modal` work.
- **Testability:** `render_breadcrumb_line` is pure and unit-testable without curses; only `draw_breadcrumb_bar` and the `render_frame` integration need the existing `StubScreen` double.

## 8. Risks & mitigations

- **Risk:** Shrinking `draw_panel`/`draw_modal`'s usable height and shifting their minimum start row by two could visually clip or shift existing rendered content in ways not covered by current tests. **Mitigation:** T2's new tests explicitly assert the new top-row boundary; existing tests for `draw_panel`/`draw_modal` (e.g. `test_ep7_t3_draw_panel.py`, `test_ep7_t2_draw_modal.py`) must still pass unmodified against the new two-row-shorter/lower-starting behavior, or be updated deliberately as part of T2, not incidentally.
- **Risk:** The sibling Navigation Key Help epic (also unbuilt) independently proposes reserving the terminal's *last* row and adding its own `history` parameter to `render_frame`; if both land without coordination, `render_frame`'s signature and `draw_panel`/`draw_modal`'s height math must compose (top-2 + bottom-1 reserved simultaneously) rather than one epic's change overwriting the other's. **Mitigation:** this spec's reservation is expressed as a fixed top offset independent of any bottom offset, and `render_frame`'s new `breadcrumb` parameter is additive to (not a replacement for) any `history` parameter the other epic adds; whichever epic is implemented second should re-run its own tests against the first epic's already-landed height math rather than assuming a clean slate.
- **Risk:** Only ever rendering `stops[-1]` means a user drilling several relations deep loses all visual trace of the intermediate hops they took, which could surprise someone expecting the full path implied by the PRD's own "Returning to a previous screen" journey. **Mitigation:** this is a direct, deliberate consequence of the PRD's Cycle 1 F2/AC5 decision, not an implementation gap; `Breadcrumb.as_list()` still retains the full stack internally, so a future epic could add a "show full path" affordance without any data-model change.

## 10. Decision log

### Revision 2 — answered

| #  | Question | Decision |
| -- | -------- | -------- |
| D1 | Whether the root label and a table/record segment ever coexist | Mutually exclusive: root label only while `Breadcrumb.as_list()` is empty; otherwise only the current table/record segment is shown |
