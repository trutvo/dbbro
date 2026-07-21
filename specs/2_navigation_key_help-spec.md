# Epic 2 — Navigation Key Help — Technical Specification

Tech spec for [`2_navigation_key_help.md`](./2_navigation_key_help.md). Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~90% after revision 1 — the exact truncation character budget and how "priority" is encoded per key are fixed here, but the visual coexistence with EP-1's (currently unbuilt) breadcrumb row is only asserted, not verified against real EP-1 code

## 1. Overview

This epic adds a one-line, always-visible "navigation key help" bar pinned to the terminal's last row, listing the currently-usable navigation keys for whatever `View` is on top of the stack (plus the globally-intercepted keys `q`/`s`/history back-forward), dropping lowest-priority entries first when the line would otherwise overflow the terminal width. Scope is `dbbro/ui/` (a new `help_bar.py` module, a small addition to the `View` protocol, and a call from `render_frame`) plus `dbbro/history/history.py` (two new pure peek methods). See PRD: [`specs/2_navigation_key_help.md`](./2_navigation_key_help.md).

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| F1 / AC1 | Help line shown on every screen | §3, §6 T2, T5 |
| F2 | Key + short verb label format | §4, §6 T1 |
| F3 / AC3 | Updates when screen's key set changes | §3, §6 T2 (recomputed every `render_frame` call, no cached state) |
| F4 / AC2 / AC6 | Omits keys not currently usable | §5, §6 T3, T4 |
| F5 / AC5 | Drops lowest-priority keys first on overflow | §4, §6 T1 |
| F6 / AC8 | Visible during loading/error states | §3, §6 T5 (modal render path) |
| N1 / AC4 | Never wraps to a second line | §4, §6 T1 |
| N2 | Fits terminal width or truncates legibly | §4, §6 T1 |
| N3 / AC7 | Own dedicated bottom line, no collision | §3 (Key architecture decision), §6 T2 |
| N4 / AC9 | Not user-toggleable, always on | §3, §6 T2 (no key or state ever disables it) |

## 3. Architecture

### Components

- **`HelpKey`** (new, `dbbro/ui/help_bar.py`) — a small frozen dataclass: `key_label: str`, `action_label: str`, `priority: int` (lower number = higher priority = kept longest under truncation).
- **`View.help_keys()`** (new, optional protocol method, mirrors the existing `consumes_navigation_keys()` pattern in `app.py:38-41`) — each view returns the list of `HelpKey` entries it currently exposes, computed fresh from its own state (so F4/AC6 "omit unusable keys" falls out naturally: a view simply doesn't include a key whose action isn't currently valid).
- **`get_help_keys(view) -> list[HelpKey]`** (new, `app.py`, same `getattr(..., default)` shape as `consumes_navigation_keys`) — views that don't define `help_keys()` contribute `[]`.
- **`global_help_keys(view, history) -> list[HelpKey]`** (new, `app.py`) — appends the keys the main loop intercepts globally (§5), so every view doesn't have to repeat them: `q` (quit) unless `consumes_navigation_keys(view)`, `s` (search) unless `consumes_navigation_keys(view)`, `←`/`→` (back/forward) only when `history.can_go_back()` / `can_go_forward()` (new peek methods, §4) return true and the view doesn't itself consume navigation keys.
- **`render_help_line(keys: list[HelpKey], width: int) -> str`** (new, `dbbro/ui/help_bar.py`) — joins `"{key_label} {action_label}"` entries with `" · "`, sorted by ascending `priority` for the fit computation, dropping the current lowest-priority (highest `priority` value) entry and recomputing until the joined string (in original left-to-right order, not priority order) fits in `width`; returns `""` if even zero keys somehow don't fit (defensive, width <= 0).
- **`draw_help_bar(screen, keys: list[HelpKey]) -> None`** (new, `dbbro/ui/screen.py`, alongside `draw_panel`/`draw_modal`) — reads `max_height, max_width = screen.getmaxyx()`, calls `render_help_line(keys, max_width)`, and `_write_line`s it at row `max_height - 1`.

### Data flow

`render_frame` (`app.py:67-77`) currently does `erase → view.render(screen) → optional modal.render(screen)`. It changes to: `erase → view.render(screen, usable_height=max_height-1) → optional modal.render(screen) → draw_help_bar(screen, get_help_keys(view) + global_help_keys(view, history))`. The help bar is drawn **last**, after any modal, so it always wins the bottom row even if a modal's box would otherwise reach it — but see the Key architecture decision below, which prevents that collision from ever needing to happen.

### Key architecture decisions

- **Reserve the bottom row by shrinking usable height, not by overlaying afterward.** `draw_panel` and `draw_modal` (`screen.py`) already derive every layout clamp from a single `max_height = screen.getmaxyx()[0]` call at their top (e.g. `visible_height = max_height - 4`, `if row >= max_height - 1: break`). Both are changed to accept the height to lay out against as `max_height - 1` (computed once in `render_frame` and threaded through `View.render(screen)` implementations, or — to avoid touching every view's `render` signature — `screen.py`'s draw functions read `getmaxyx()` internally and simply subtract 1 from the height before doing their existing math). *(Architecture advisor: this reuses the exact height-clamping pattern already present in every draw function in screen.py, so reserving the help bar's row is a minimal, consistent extension of existing conventions rather than a new layout mechanism, subwindow model, or fragile overwrite-and-hope ordering.)* This was evaluated against three alternatives — drawing the help bar over unclamped content, introducing `curses.derwin` subwindows (unused anywhere else in this hand-rolled renderer), and monkey-patching `getmaxyx()` — and rejected all three per the advisor's finding that they either race with existing content or deviate from the codebase's established single-source-of-truth height pattern.
- **Global keys are assembled once in `app.py`, not duplicated per-view.** `q`, `s`, and history back/forward are already intercepted centrally in `run()`'s main loop (`app.py:127-142`); `global_help_keys()` mirrors that same set of conditions (`consumes_navigation_keys`, `history.can_go_back/forward`) so the help line can never show a global key a view-specific interception would actually swallow, or vice versa.
- **No caching of the help line.** `render_frame` runs on every keypress/resize already (`app.py:114-145`); recomputing `help_keys()` fresh each call is O(number of keys) and trivially satisfies F3/AC3 without invalidation logic.

## 4. Data model

- **`HelpKey`** — `key_label: str` (e.g. `"↑/↓"`, `"enter"`, `"esc"`, `"q"`), `action_label: str` (e.g. `"move"`, `"open"`, `"back"`, `"quit"`), `priority: int` — lower values are kept first when truncating; suggested convention (not enforced by types, just usage): `0` = move/select, `1` = open/confirm, `2` = back/cancel, `3` = quit/global. No persistence, no lifecycle — a `HelpKey` list is recomputed fresh on every `render_frame` call and discarded immediately after use.
- **`History` gains two pure peek methods** (`dbbro/history/history.py`, alongside `go_back`/`go_forward`): `can_go_back() -> bool` (`self._position > 0`) and `can_go_forward() -> bool` (`self._position < len(self._entries) - 1`) — read-only, no side effects, matching the class's existing "never imports or calls into ui/" docstring constraint.
- **Truncation is character-count based**, not a fixed key-count: `render_help_line` fits as many whole `"{key_label} {action_label}"` segments (joined by `" · "`) as the terminal's current width allows, dropping one lowest-priority segment at a time — this resolves the PRD's one flagged residual gap (exact truncation threshold) by defining it as "whatever fits `max_width - 1` columns of the terminal's *current* width, recomputed on every render," rather than a fixed constant, since the PRD explicitly left this to implementation.

## 5. API / interfaces

```python
# dbbro/ui/help_bar.py
@dataclass(frozen=True)
class HelpKey:
    key_label: str
    action_label: str
    priority: int  # lower = higher priority = dropped last

def render_help_line(keys: list[HelpKey], width: int) -> str: ...

# dbbro/ui/screen.py
def draw_help_bar(screen, keys: list[HelpKey]) -> None: ...

# dbbro/ui/app.py
def get_help_keys(view) -> list[HelpKey]: ...          # mirrors consumes_navigation_keys()
def global_help_keys(view, history: History) -> list[HelpKey]: ...
def render_frame(stdscr, stack: ViewStack, pending_modal, history: History) -> None: ...
    # signature grows a `history` param so it can call global_help_keys()

# dbbro/history/history.py (History class, new methods)
def can_go_back(self) -> bool: ...
def can_go_forward(self) -> bool: ...

# Each existing View gains an optional method (duck-typed, like consumes_navigation_keys):
class SomeView:
    def help_keys(self) -> list[HelpKey]: ...
```

View-by-view `help_keys()` contents (derived from each view's already-known `handle_key` branches):

- `TableView` (`table_view.py`): `↑/↓ move`, `enter open` (only if `self.fields[self.selected]` is a `RelationField` — F4/AC6: "open" is omitted on non-relation fields).
- `SelectionList` (`selection_list.py`): `↑/↓ move`, `enter select`, `esc back`.
- `SearchSelectionDialog` / `SearchValuePrompt` (`search_dialog.py`, `search_prompt.py`): whatever their own `handle_key` already supports (e.g. `enter search`, `esc back`) — enumerated per view during T3 by reading each `handle_key` method, not invented.
- `ErrorNotice` (`modals.py`): `enter dismiss` — modals are drawn on top of the stack but the help bar must still reflect the modal's own dismiss key while it's pending, not the view underneath (F6/AC8); `render_frame` passes `get_help_keys(pending_modal or stack.current)`.
- `QuitConfirmation` (`modals.py`): `enter quit`, `esc cancel`.

## 6. Implementation plan (TDD)

### T1. `HelpKey` + `render_help_line` truncation logic       (closes: F2, F5, N1, N2, AC4, AC5)
- Failing tests to write first:
  - `tests/test_ep2_t1_render_help_line.py::test_joins_keys_with_separator` — three `HelpKey`s fit comfortably, expect `"↑/↓ move · enter open · q quit"`.
  - `test_drops_lowest_priority_first_when_overflowing` — narrow width forces dropping the highest-`priority`-number entry(ies) first, keeping order of remaining entries.
  - `test_never_exceeds_given_width` — fuzz over widths 0..40, assert `len(result) <= width` always.
  - `test_empty_keys_returns_empty_string`.
- Production code to make them pass:
  - `dbbro/ui/help_bar.py`: `HelpKey` dataclass, `render_help_line(keys, width)`.
- Refactor step:
  - Extract the "try full join, else drop-lowest-and-retry" loop into a small private helper if it grows past ~10 lines.

### T2. `draw_help_bar` + bottom-row reservation in `screen.py`   (closes: F1, N3, AC1, AC7)
- Failing tests to write first:
  - `tests/test_ep2_t2_draw_help_bar.py::test_writes_help_line_at_last_row` — using the existing `StubScreen` double, assert `addstr` was called with `y == max_height - 1`.
  - `test_draw_panel_reserves_bottom_row` — assert `draw_panel`'s last content row is now `max_height - 2` (one row higher than before), i.e. never writes to `max_height - 1`.
  - `test_draw_modal_reserves_bottom_row` — same assertion for `draw_modal`.
- Production code to make them pass:
  - `dbbro/ui/screen.py`: add `draw_help_bar(screen, keys)`; change `draw_panel`/`draw_modal` to compute their internal `max_height` as `getmaxyx()[0] - 1` before doing existing clamp math.
- Refactor step:
  - Factor the `usable_height = screen.getmaxyx()[0] - 1` line into a tiny shared helper (e.g. `_usable_height(screen)`) used by all three draw functions, to avoid the "-1" magic number appearing three times.

### T3. `help_keys()` on each existing `View`                   (closes: F2, F4, AC2, AC6)
- Failing tests to write first:
  - `tests/test_ep2_t3_view_help_keys.py::test_table_view_omits_open_when_field_not_relation` — build a `TableView` with a non-relation field selected, assert `help_keys()` has no `"open"` entry.
  - `test_table_view_includes_open_when_relation_field_selected`.
  - `test_selection_list_help_keys_contents`.
  - `test_search_dialog_help_keys_contents`, `test_search_prompt_help_keys_contents` (per each view's actual `handle_key` branches, enumerated by reading the current source, not invented).
  - `test_error_notice_and_quit_confirmation_help_keys`.
- Production code to make them pass:
  - `help_keys(self) -> list[HelpKey]` added to `TableView`, `SelectionList`, `SearchSelectionDialog`, the view(s) in `search_prompt.py`, `ErrorNotice`, `QuitConfirmation`.
- Refactor step:
  - If two or more views share an identical `↑/↓ move` + `esc back` shape, factor a small module-level constant/helper in `help_bar.py` (e.g. `MOVE_KEYS`) rather than repeating literal `HelpKey(...)` construction.

### T4. `History.can_go_back` / `can_go_forward`                (closes: F4, AC6 — for the back/forward keys specifically)
- Failing tests to write first:
  - `tests/test_ep2_t4_history_can_navigate.py::test_can_go_back_false_when_at_start`
  - `test_can_go_back_true_after_multiple_entries`
  - `test_can_go_forward_false_at_most_recent_entry`
  - `test_can_go_forward_true_after_going_back`
- Production code to make them pass:
  - `dbbro/history/history.py`: `can_go_back()`, `can_go_forward()` on `History`.
- Refactor step:
  - None expected; two one-line boolean methods.

### T5. Wire `global_help_keys` + `render_frame` integration      (closes: F1, F3, F6, AC1, AC3, AC8, AC9)
- Failing tests to write first:
  - `tests/test_ep2_t5_render_frame_help_bar.py::test_help_bar_present_on_initial_render` — run `ui_app.run(StubScreen(...), config, conn=None)` (existing loop-driving fixture pattern) and assert the last row written contains recognizable key labels.
  - `test_help_bar_updates_after_navigating_to_different_view` — push a different view (e.g. follow a relation into a `TableView`) and assert the help line's content changed.
  - `test_help_bar_visible_during_pending_error_modal` — trigger `OperationFailedError`, assert the help bar still renders (shows the modal's `enter dismiss`, not the view underneath).
  - `test_help_bar_visible_during_quit_confirmation`.
  - `test_no_key_or_state_hides_help_bar` — exercise every reachable state transition in the existing integration test fixtures and assert `draw_help_bar` (or its output row) is always non-empty.
- Production code to make them pass:
  - `dbbro/ui/app.py`: `get_help_keys(view)`, `global_help_keys(view, history)`, update `render_frame` to accept `history` and call `draw_help_bar(stdscr, get_help_keys(pending_modal or stack.current) + global_help_keys(stack.current, history))`; update the two call sites in `run()` (initial render + main loop) to pass `history`.
- Refactor step:
  - Once T1–T5 are green, re-read `render_frame`'s docstring and update it to describe the help-bar behavior (it currently only describes erase/view/modal), keeping doc and code in sync.

## 7. Non-functional concerns

- **Legibility (N2):** truncation always keeps whole `"key action"` segments, never mid-word cuts, since `render_help_line` drops entire `HelpKey` entries rather than character-slicing the joined string.
- **No wrapping (N1/AC4):** `draw_help_bar` writes a single `addstr` call per frame at one fixed row; curses truncates rather than wraps by default for a line that reaches the window edge, and `render_help_line` additionally pre-fits the content to `max_width` so no addstr call is ever asked to exceed the row's width in the first place.
- **Always-on (N4/AC9):** no toggle key, no config flag, no state field controls whether the help bar renders — `render_frame` calls `draw_help_bar` unconditionally on every frame, matching the "no expert mode" requirement.
- **Performance:** `help_keys()` implementations are O(1)–O(number of fields), called once per keypress; negligible relative to existing per-frame `draw_panel`/`draw_modal` work.
- **Testability:** all new logic (`render_help_line`, `HelpKey`, `can_go_back/forward`, each view's `help_keys()`) is pure and unit-testable without curses; only `draw_help_bar` and the `render_frame` integration need the existing `StubScreen` double.

## 8. Risks & mitigations

- **Risk:** Shrinking `draw_panel`/`draw_modal`'s usable height by one row could visually shift or clip existing rendered content in ways not covered by current tests. **Mitigation:** T2's new tests explicitly assert the new last-content-row boundary; existing tests for `draw_panel`/`draw_modal` (e.g. `test_ep7_t3_draw_panel.py`) must still pass unmodified against the new one-row-shorter behavior, or be updated deliberately as part of T2, not incidentally.
- **Risk:** EP-1 (visible breadcrumb, not yet built) may independently claim a top-of-screen row using a similar height-reservation approach; if EP-1 lands first or concurrently, the two epics' height math must compose (top row + bottom row both reserved) rather than each assuming full height. **Mitigation:** this spec's height reservation is expressed as "subtract 1 from usable height," which composes additively with any future top-row reservation; call this out explicitly if/when EP-1's spec is written.
- **Risk:** Global key set (`q`/`s`/history) duplicating the exact conditions already in `run()`'s main loop (`consumes_navigation_keys`, `can_go_back/forward`) could drift out of sync if one is updated without the other. **Mitigation:** `global_help_keys()` takes the same `view` and calls the same `consumes_navigation_keys(view)` helper already used by `run()`, rather than re-deriving the condition independently.

## 9. Open architecture decisions

None. The one high-impact decision identified during drafting (how to reserve the bottom row without colliding with existing panel/modal rendering) was resolved with the architecture-advisor's input and recorded as a Key architecture decision in §3 rather than left open, since the PRD gives no signal that this choice should be deferred to the user and a concrete, low-risk answer was available.
