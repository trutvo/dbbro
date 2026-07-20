# Epic 7 — Terminal Rendering — Technical Specification

Tech spec for `7_terminal_rendering.md`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~91% after revision 1 — architecture, data model, and TDD task plan are concrete enough to start T1; the main residual gap is that curses' resize signal (`KEY_RESIZE`) behavior can vary subtly across terminal emulators, so T6's resize test is necessarily a best-effort simulation rather than a guarantee across every real terminal.

## 1. Overview

This spec implements the five `render()` stubs left as `pass` across the whole UI layer (`SearchSelectionDialog`, `SearchValuePrompt`, `TableView`, `SelectionList`, `ErrorNotice`), plus the terminal-size handling (resize, overflow truncation) and screen-consistency guarantee the PRD requires. It introduces one new module, `dbbro/ui/screen.py`, holding the shared drawing/scrolling/truncation primitives every view's `render()` calls into, so the box-drawing logic exists in exactly one place rather than five. Out of scope: any change to key handling, selection logic, or what data a view holds (already implemented by Epics 2/3/5) — this epic only draws it. See `7_terminal_rendering.md`.

**Correction to a PRD assumption, flagged here rather than silently worked around:** the PRD's Q2/FR3 assume the match/selection list "already scrolls." In the actual codebase, `dbbro/ui/selection_list.py::SelectionList` has no scroll-offset state at all — only `TableView` does (`self.scroll_offset`, `_update_scroll()`). This spec adds equivalent scroll-offset tracking to both `SelectionList` and `SearchSelectionDialog` (neither of which has it today) using a shared helper, so the PRD's requirement is still met — it just isn't literally copying pre-existing behavior, since that behavior didn't yet exist outside `TableView`.

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| FR1  | Draw search selection dialog as modal listing pairs | §3, §6 T4 |
| FR2  | Highlighted pair distinguished (reverse video) | §3, §6 T2, T4 |
| FR3  | Dialog scrolls when pairs exceed modal height | §3, §6 T1, T4 |
| FR4  | Draw search value prompt as modal w/ label + typed value | §6 T4 |
| FR5  | Draw table view as bordered panel w/ table name header | §3, §6 T3, T4 |
| FR6  | One row per configured column, name + value | §6 T3, T4 |
| FR7  | Selected field distinguished (reverse video) | §6 T3, T4 |
| FR8  | Relation field value in `<table>[<fk>]` format | §6 T4 (pre-existing `fields.py`, drawn as-is) |
| FR9  | Match/selection list drawn as modal, one row per candidate | §3, §6 T2, T4 |
| FR10 | Highlighted candidate row distinguished (reverse video) | §6 T2, T4 |
| FR11 | Error notice drawn as modal describing the problem | §6 T2, T4 |
| FR12 | Error notice stays visible until dismissed | §6 T4 (pre-existing dismiss logic, unaffected) |
| FR13 | Only active screen visibly drawn, no stale content | §3, §6 T5 |
| FR14 | Redraw active screen on terminal resize | §3, §6 T6 |
| FR15 | Truncate content wider than terminal width | §3, §6 T1, T2, T3 |
| NFR1 | No perceptible lag between action and redraw | §7 |
| NFR2 | Exact Unicode box-drawing chars, no ASCII fallback | §3, §4, §6 T2, T3 |
| NFR3 | Screen stays correctly sized/drawn after resize | §6 T6 |
| AC1  | Dialog modal lists every search pair | §6 T4 |
| AC2  | Highlighted pair in reverse video | §6 T2, T4 |
| AC3  | Dialog scrolls to keep highlighted pair visible | §6 T1, T4 |
| AC4  | Value prompt modal shows label + live typed value | §6 T4 |
| AC5  | Table view panel w/ table name header | §6 T3, T4 |
| AC6  | One row per column, name + value | §6 T3, T4 |
| AC7  | Selected field in reverse video | §6 T3, T4 |
| AC8  | Relation field in `<table>[<fk>]` format | §6 T4 |
| AC9  | Match/selection list drawn as modal, one row per candidate | §6 T2, T4 |
| AC10 | Highlighted row in reverse video | §6 T2, T4 |
| AC11 | Error notice modal describes the problem | §6 T2, T4 |
| AC12 | Error notice stays visible until Return | §6 T4 |
| AC13 | No stale content across screen switches | §6 T5 |
| AC14 | Resize redraws active screen to new size | §6 T6 |
| AC15 | Content wider than terminal is truncated | §6 T1, T2, T3 |

## 3. Architecture

```
dbbro/
  ui/
    screen.py          # new: truncate(), update_scroll(), draw_modal(), draw_panel()
    view_stack.py       # unchanged
    search_dialog.py     # render() implemented via screen.draw_modal; adds scroll_offset
    search_prompt.py     # render() implemented via screen.draw_modal
    selection_list.py    # render() implemented via screen.draw_modal; adds scroll_offset
    table_view.py         # render() implemented via screen.draw_panel (existing scroll_offset reused)
    modals.py             # ErrorNotice.render() implemented via screen.draw_modal
    app.py                # main loop: erase-before-render (FR13) + KEY_RESIZE handling (FR14)
```

Flow: every view's `render(screen)` becomes a thin call into one of two shared primitives in the new `dbbro/ui/screen.py`:

- **`draw_modal(screen, lines, highlighted_index=None)`** — used by `SearchSelectionDialog`, `SearchValuePrompt`, `SelectionList`, and `ErrorNotice`. Computes a box width from the longest line (truncated to the terminal's current width per FR15/NFR2), draws the double-line modal border using the briefing's exact modal character set, writes each line (truncating any that don't fit), and — if `highlighted_index` is given — draws that line with `curses.A_REVERSE` (FR2/FR10, reverse video per the PRD's Cycle 1 Q1 decision).
- **`draw_panel(screen, header, rows, highlighted_index, scroll_offset)`** — used by `TableView` only. Draws the single-line panel border using the briefing's exact panel character set, a header row (table name), then one two-column row per `(name, value)` pair in `rows[scroll_offset : scroll_offset + visible_height]`, truncating any value that doesn't fit and reverse-videoing the row at `highlighted_index` (FR7/AC7).

Both primitives take the **real, current** terminal size from `screen.getmaxyx()` at call time — not a value cached at construction — so a box is always sized correctly for whatever the terminal looks like *right now*, including immediately after a resize (FR14/NFR3), without any view needing to know about resize events itself.

Scrolling (FR3/AC3, FR9/AC9): a single shared function, `screen.update_scroll(selected, offset, visible_height) -> int`, is the same logic already written once in `TableView._update_scroll` — this spec extracts it into `screen.py` and adds equivalent `scroll_offset` state (initialized to `0`) to `SearchSelectionDialog` and `SelectionList`, calling `update_scroll` from their Up/Down handlers exactly as `TableView` already does. `draw_modal`/`draw_panel` use the resulting offset to slice which lines/rows are actually visible this frame.

Screen consistency (FR13/AC13): rather than have every view remember to clear stale content, the main loop (`dbbro/ui/app.py::run`) calls `stdscr.erase()` once per frame, immediately before calling `stack.current.render(stdscr)` (and the pending modal's `render`, if any) — a single, structural fix that makes "no stale content" true by construction regardless of which view is active.

Resize handling (FR14/AC14, NFR3): curses' `getch()` returns `curses.KEY_RESIZE` when the terminal is resized (ncurses translates `SIGWINCH` into this keycode when using `curses.wrapper`, which the app already does). The main loop adds one branch: on `KEY_RESIZE`, call `curses.update_lines_cols()` and immediately re-render the current screen — no other state changes, since `draw_modal`/`draw_panel` already recompute sizing from `getmaxyx()` on every call.

**Key architecture decisions:**

- **One shared `screen.py` module owns all drawing, not five independent implementations** — keeps the box-drawing character sets, truncation, highlighting, and scrolling logic in one place, so a future change to (for example) how truncation works doesn't need to be repeated in five files.
- **Terminal size is read fresh from `getmaxyx()` on every render call, never cached** — this is what makes resize handling (FR14) almost free: nothing needs to explicitly "know" a resize happened beyond re-triggering a render, since every render already recomputes sizing from the current, live terminal dimensions.
- **`update_scroll` is extracted from `TableView` into `screen.py` and reused by `SearchSelectionDialog`/`SelectionList`**, rather than each view reimplementing the same clamp-to-viewport math — this directly resolves the discrepancy noted in §1 (the PRD assumed this scrolling already existed in `SelectionList`; it didn't, so this spec adds it via the same shared function `TableView` already used).
- **`stdscr.erase()` once per frame in the main loop is the single mechanism for FR13**, not per-view clearing — a view never needs to know or care what was drawn before it.
- **No ASCII fallback path exists anywhere in `screen.py` (NFR2)** — the box-drawing character constants are the briefing's exact Unicode characters, used unconditionally.

## 4. Data model

`dbbro/ui/screen.py` holds two module-level constant dicts, not classes (no new persisted/runtime entities are introduced by this epic):

```python
PANEL_CHARS = {
    "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
    "h": "─", "v": "│", "cross": "┼", "t_down": "┬", "t_up": "┴",
    "t_right": "├", "t_left": "┤",
}
MODAL_CHARS = {
    "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
    "h": "═", "v": "║", "cross": "╬", "t_down": "╦", "t_up": "╩",
    "t_right": "╠", "t_left": "╣",
}
```

(Only the corner/edge characters actually used by `draw_modal`/`draw_panel`'s single-box-per-screen layout are exercised; the cross/tee characters are included for completeness against the briefing's full character set but unused until a future epic needs a multi-cell grid.)

## 5. API / interfaces

`dbbro/ui/screen.py`:
```python
def truncate(text: str, width: int) -> str:
    """Returns text unchanged if len(text) <= width, else text[:width]."""

def update_scroll(selected: int, offset: int, visible_height: int) -> int:
    """Same clamp-to-viewport logic as TableView._update_scroll: returns a new
    offset such that `selected` stays within [offset, offset + visible_height)."""

def draw_modal(screen, lines: list[str], highlighted_index: int | None = None) -> None:
    """Draws a double-line modal box sized to the longest (terminal-width-
    truncated) line in `lines`, drawing lines[highlighted_index] (if given)
    with curses.A_REVERSE."""

def draw_panel(
    screen, header: str, rows: list[tuple[str, str]],
    highlighted_index: int, scroll_offset: int,
) -> None:
    """Draws a single-line-bordered panel: `header` as the title row, then
    rows[scroll_offset:scroll_offset+visible_height] as name/value rows
    (visible_height derived from screen.getmaxyx()), truncating any value
    that doesn't fit, reverse-videoing the row at `highlighted_index`."""
```

Each view's `render(screen)` changes from `pass` to a direct call:
```python
# search_dialog.py::SearchSelectionDialog.render
def render(self, screen) -> None:
    lines = [f"{table}.{column}" for table, column in self.pairs]
    screen.erase()  # belt-and-suspenders; app.py already erases once per frame
    from .screen import draw_modal
    draw_modal(screen, lines[self.scroll_offset:], highlighted_index=self.highlighted - self.scroll_offset)
```
(`table_view.py`, `selection_list.py`, `search_prompt.py`, `modals.py` follow the same pattern, calling `draw_panel`/`draw_modal` with their own state.)

## 6. Implementation plan (TDD)

### T1. `truncate` and `update_scroll` pure functions            (closes: FR3, FR15, AC3, AC15)
- Failing tests to write first:
  - `test_truncate_returns_text_unchanged_when_within_width`
  - `test_truncate_cuts_text_to_width_when_too_long`
  - `test_update_scroll_moves_offset_up_when_selection_above_viewport`
  - `test_update_scroll_moves_offset_down_when_selection_below_viewport`
  - `test_update_scroll_leaves_offset_unchanged_when_selection_already_visible`
- Production code to make them pass:
  - `dbbro/ui/screen.py::truncate`, `update_scroll`

### T2. `draw_modal` (search dialog, value prompt, match list, error notice)    (closes: FR2, FR9, FR10, FR11, FR15, NFR2, AC2, AC9, AC10, AC11, AC15)
- Failing tests to write first:
  - `test_draw_modal_writes_every_line` (stub `screen` object recording `addstr`/`addnstr` calls; assert each line's text appears)
  - `test_draw_modal_draws_double_line_border_characters` (assert the modal's exact corner/edge chars from `MODAL_CHARS` appear in the recorded calls)
  - `test_draw_modal_applies_reverse_video_only_to_highlighted_line`
  - `test_draw_modal_truncates_lines_wider_than_terminal_width` (stub `screen.getmaxyx()` returns a narrow width)
- Production code to make them pass:
  - `dbbro/ui/screen.py::draw_modal`

### T3. `draw_panel` (table view)            (closes: FR5, FR6, FR7, FR15, NFR2, AC5, AC6, AC7, AC15)
- Failing tests to write first:
  - `test_draw_panel_writes_header_and_one_row_per_column`
  - `test_draw_panel_draws_single_line_border_characters`
  - `test_draw_panel_applies_reverse_video_only_to_highlighted_row`
  - `test_draw_panel_truncates_values_wider_than_terminal_width`
  - `test_draw_panel_shows_only_rows_within_scroll_window`
- Production code to make them pass:
  - `dbbro/ui/screen.py::draw_panel`

### T4. Wire every view's `render()` to the shared primitives, add missing scroll state    (closes: FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12, AC1–AC12)
- Failing tests to write first:
  - `test_search_selection_dialog_render_calls_draw_modal_with_all_pairs_and_highlighted_index`
  - `test_search_selection_dialog_scroll_offset_updates_on_down_up` (new state, mirroring `TableView`)
  - `test_search_value_prompt_render_calls_draw_modal_with_label_and_buffer`
  - `test_table_view_render_calls_draw_panel_with_fields_and_selected_index`
  - `test_selection_list_render_calls_draw_modal_with_records_and_highlighted_index`
  - `test_selection_list_scroll_offset_updates_on_down_up` (new state, mirroring `TableView`)
  - `test_error_notice_render_calls_draw_modal_with_message`
- Production code to make them pass:
  - `search_dialog.py::SearchSelectionDialog.render` + new `scroll_offset` field, updated in `handle_key` via `screen.update_scroll`
  - `search_prompt.py::SearchValuePrompt.render`
  - `table_view.py::TableView.render`
  - `selection_list.py::SelectionList.render` + new `scroll_offset` field, updated in `handle_key` via `screen.update_scroll`
  - `modals.py::ErrorNotice.render`

### T5. Screen consistency: erase-before-render in the main loop            (closes: FR13, AC13)
- Failing tests to write first:
  - `test_main_loop_erases_screen_before_each_render` (stub `stdscr`; assert `erase()` is called before every `render()` call in a sequence of key presses that switch views)
- Production code to make them pass:
  - `dbbro/ui/app.py::run` — call `stdscr.erase()` immediately before each render step

### T6. Resize handling            (closes: FR14, NFR3, AC14)
- Failing tests to write first:
  - `test_main_loop_calls_update_lines_cols_and_rerenders_on_key_resize` (stub `stdscr.getch()` to return `curses.KEY_RESIZE` once; assert `curses.update_lines_cols` was called and the current view's `render` ran again)
- Production code to make them pass:
  - `dbbro/ui/app.py::run` — `elif key == curses.KEY_RESIZE: curses.update_lines_cols()` branch, falling through to the existing per-frame render step

### Refactor step (after T6)
- Once T1–T6 are green, review whether `search_dialog.py`/`selection_list.py`'s newly-added `scroll_offset` + Up/Down handling has converged to identical code (both now: `self.highlighted = (self.highlighted ± 1) % len(items); self.scroll_offset = update_scroll(...)`); if so, consider whether a tiny shared mixin/helper is warranted — do not pre-extract before confirming the duplication is real.

## 7. Non-functional concerns

- **No perceptible lag (NFR1):** every render is a direct, synchronous sequence of `curses` draw calls with no I/O, network, or sleep in the path — satisfied by construction; no dedicated test beyond T2–T4's render-call assertions, since there is no asynchronous step to race against.
- **Unicode required, no ASCII fallback (NFR2):** `PANEL_CHARS`/`MODAL_CHARS` are the only character sets `screen.py` ever draws with; there is no conditional/fallback code path, so this is enforced by the absence of an alternative rather than a runtime check.
- **Resize robustness (NFR3):** because `draw_modal`/`draw_panel` read `screen.getmaxyx()` fresh every call rather than caching terminal dimensions, correctness after a resize follows directly from T2/T3's existing tests (which already vary the stubbed terminal size) plus T6's resize-triggers-rerender test — no separate "still correct after resize" test category is needed.

## 8. Risks & mitigations

- Risk: the PRD's premise that the match/selection list "already scrolls" doesn't match the actual code (`SelectionList` has no scroll state). Mitigation: called out explicitly in §1 and addressed directly in T4 by adding the missing `scroll_offset` state via the same shared `update_scroll` helper `TableView` already uses — no product requirement changes, only a factual correction to how it's satisfied.
- Risk: curses' `KEY_RESIZE` delivery can be inconsistent across terminal emulators/multiplexers (e.g. some tmux/screen configurations). Mitigation: out of scope to guarantee for every terminal; T6's test simulates the documented `curses` mechanism, which is the standard approach and the best any pure-curses implementation can rely on.
- Risk: testing curses rendering without a real terminal requires stubbing `screen.addstr`/`addnstr`/`getmaxyx`/`erase`, which could drift from real curses' actual argument conventions if done carelessly. Mitigation: stub objects in T2–T6's tests should record calls in the same shape real curses methods accept (e.g. `addstr(y, x, text, attr=0)`), so a manual smoke test in a real terminal (recommended once T1–T6 are green) is the only remaining verification step, consistent with Epics 2/3's original "reserve real curses.wrapper execution for a manual smoke test" approach.

## 9. Open architecture decisions

_None — every technical choice this epic needs (shared drawing module, scroll extraction, erase-before-render, `KEY_RESIZE` handling) follows directly from the PRD's already-resolved decisions and curses' standard idioms; none of them is a high-impact choice that warrants separate user sign-off._
