# Epic 2 — Record Search — Technical Specification

Tech spec for `2_record_search.md`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~94% after revision 2 — D1 is resolved (`curses`) and already reflected in §3; architecture, data model, and the TDD task plan are concrete enough to start T1. The remaining gap is external to this spec: Epic 4's spec recommends `prompt_toolkit` instead of `curses`, a cross-epic conflict that must be reconciled before implementation, though it does not block starting T1 here.

## 1. Overview

This spec covers the search selection dialog, search value prompt, and match list modals that let an operator pick a searchable (table, column) pair, enter a value, and reach either a single match, a match list, or a no-match outcome. It builds `dbbro/cli.py::run_ui`'s currently-unimplemented body into a curses-based modal UI shell, and exposes the lookup/match-outcome logic other epics (3, 5) will render into. Out of scope: rendering a matched record's fields (EP-3), browsing history (EP-4), and error popup presentation (EP-5) — this epic only decides *that* a no-match is an error condition, not how it's drawn. See `2_record_search.md`.

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| FR1  | Derive full searchable pairs list on startup, show before other interaction | §3, §6 T1 |
| FR2  | Each dialog entry identifies table + column | §4, §6 T1 |
| FR3  | Up/Down moves highlight in search selection dialog | §6 T2 |
| FR4  | Return confirms highlighted pair, opens value prompt | §6 T2 |
| FR5  | Escape closes selection dialog, returns to previous view | §6 T2, T5 |
| FR6  | Value prompt shown after pair selected | §6 T3 |
| FR7  | Empty value rejected on submit | §6 T3 |
| FR8  | Non-empty submit triggers exact-match lookup on selected table/column | §5, §6 T4 |
| FR9  | Escape in value prompt cancels back to selection dialog | §6 T3 |
| FR10 | Exactly one match → proceed to record view | §5, §6 T4 |
| FR11 | Multiple matches → show match list | §5, §6 T4 |
| FR12 | No match → show error popup naming table/column/value | §5, §6 T4 |
| FR13 | Match list row shows every configured column + value | §4, §6 T6 |
| FR14 | Up/Down moves highlight in match list, unlimited scroll | §6 T6 |
| FR15 | Return on match list proceeds to record view (same as single match) | §6 T6 |
| FR16 | Escape on match list returns to pre-search view without picking | §6 T6 |
| FR17 | `s` opens search selection dialog from anywhere | §3, §6 T5 |
| FR18 | Reopening via `s` shows same pairs, highlight on first | §6 T5 |
| FR19 | Reopening via `s` mid-entry discards in-progress value | §6 T5 |
| NFR1 | Search selection dialog is the first usable UI at startup | §3, §6 T1 |
| NFR2 | `s` works regardless of current view | §3, §6 T5 |
| AC1  | Lists exactly the declared searchable pairs, table+column each | §6 T1 |
| AC2  | Table with no search columns contributes nothing | §6 T1 |
| AC3  | Down/Up moves highlight in selection dialog | §6 T2 |
| AC4  | Return opens value prompt labeled with table/column | §6 T2 |
| AC5  | Escape closes selection dialog, returns to previous view | §6 T2, T5 |
| AC6  | Non-empty submit triggers exact-match lookup | §6 T3, T4 |
| AC7  | Empty submit rejected, no lookup | §6 T3 |
| AC8  | Escape in value prompt returns to selection dialog, no lookup | §6 T3 |
| AC9  | Exactly one match → proceeds to that record's view | §6 T4 |
| AC10 | More than one match → match list shown | §6 T4 |
| AC11 | No match → error popup naming table/column/value | §6 T4 |
| AC12 | `s` opens selection dialog from any other view | §6 T5 |
| AC13 | Reopened dialog lists same pairs, highlight on first | §6 T5 |
| AC14 | Reopening via `s` mid-entry discards in-progress value | §6 T5 |
| AC15 | Match list row shows every configured column + value | §6 T6 |
| AC16 | Down/Up moves highlight in match list, scrolls, no limit | §6 T6 |
| AC17 | Return on highlighted match proceeds to that record's view | §6 T6 |
| AC18 | Escape on match list returns to pre-search view, no pick | §6 T6 |

## 3. Architecture

```
dbbro/
  config/                  # unchanged (EP-1)
  ui/
    __init__.py
    screen.py              # curses window lifecycle: init/wrap, box-drawing helpers
    view_stack.py           # ViewStack: push/pop/current, holds the modal/view history
    keys.py                 # key constants (UP, DOWN, RETURN, ESCAPE, ord('s'))
    search_dialog.py        # SearchSelectionDialog(view): renders pairs, Up/Down/Return/Escape
    search_prompt.py        # SearchValuePrompt(view): text entry, Return/Escape/empty-reject
    match_list.py            # MatchListView(view): scrollable list, Up/Down/Return/Escape
  search/
    __init__.py
    lookup.py               # exact-match lookup against the database for (table, column, value)
    models.py               # SearchOutcome: NoMatch | SingleMatch(record) | MultipleMatches(records)
  cli.py                    # run_ui(config) now builds the curses app and enters the main loop
```

Flow: `cli.py::run_ui(config)` wraps `curses.wrapper(app_main, config)`. `app_main` builds a `ViewStack` and pushes a `SearchSelectionDialog` built from `config.searchable_pairs()` — this is the only view at startup (NFR1), so nothing else can render before it. The main loop reads one key at a time from the top-of-stack view and dispatches it: the view returns either `None` (stay), a new view to push (`Transition.push(view)`), or a signal to pop (`Transition.pop()`). Pressing `s` is intercepted by the main loop itself, *before* handing the key to the current view, so it works regardless of which view is on top (FR17/NFR2) — it clears any view stacked above the underlying non-search view and pushes a fresh `SearchSelectionDialog`, discarding whatever the previous top view held (FR19). Confirming a pair pushes a `SearchValuePrompt`; confirming a non-empty value calls `search.lookup.find_matches(config, table, column, value)`, which returns a `SearchOutcome`. The main loop maps `SingleMatch` to popping back to (eventually) EP-3's table view, `MultipleMatches` to pushing a `MatchListView`, and `NoMatch` to pushing whatever EP-5's error view becomes — this epic defines the `NoMatch` outcome and its required table/column/value payload, not the popup's rendering.

**Key architecture decisions:**

- **`curses` (stdlib) is the TUI foundation (D1)** — see the architecture-advisor consultation in §9; no new runtime dependency, and manual window control is the most direct way to reproduce the PRD's literal box-drawing (`║`, `═`, `┌─┬─┐`) modal mockups.
- **A single `ViewStack` models all modals as pushable/poppable views**, so search selection → value prompt → match list is just three stack frames; EP-3's table view and EP-5's error popup slot into the same stack later without changing this epic's dispatch loop.
- **`s` is intercepted by the main loop, not by individual views**, so every current and future view automatically supports reopening search without each view needing its own `s` handler — this directly satisfies FR17/NFR2 ("regardless of what view is on screen") without duplicating the check.
- **Lookup logic (`search/lookup.py`) is separated from rendering (`ui/`)**, returning a plain `SearchOutcome` value rather than mutating UI state directly, so match-count branching (FR10/FR11/FR12) is unit-testable without a curses screen.

## 4. Data model

`search/models.py`:
- `SearchOutcome` — tagged union via a small class hierarchy: `NoMatch(table: str, column: str, value: str)`, `SingleMatch(table: str, record: dict[str, object])`, `MultipleMatches(table: str, records: list[dict[str, object]])`.
- A `record` (and each entry of `records`) is a `dict[str, object]` keyed by every column configured on that `Table` (per EP-1's `Table.columns`), satisfying FR13/AC15 — the match list needs no separate "display row" type since it renders the same dict shape EP-3 will consume.

`ui/view_stack.py`:
- `ViewStack` — `frames: list[View]`; `push(view)`, `pop()`, `current -> View`.
- `View` (protocol) — `render(screen) -> None`, `handle_key(key: int) -> Transition | None`.
- `Transition` — `PUSH(view)` | `POP` | `NONE`, returned by `handle_key` to tell the main loop what to do.

## 5. API / interfaces

`search/lookup.py`:
```python
def find_matches(config: Config, table: str, column: str, value: str) -> SearchOutcome:
    """Exact-match lookup of `value` in `table.column`.

    Returns NoMatch, SingleMatch, or MultipleMatches depending on the
    number of rows found. Raises no exception for zero matches — that is
    a normal SearchOutcome, not a failure of this function.
    """
```

`ui/search_dialog.py`:
```python
class SearchSelectionDialog(View):
    def __init__(self, pairs: list[tuple[str, str]]): ...
    def handle_key(self, key: int) -> Transition | None:
        """UP/DOWN move highlight; RETURN -> Transition.PUSH(SearchValuePrompt(pair));
        ESCAPE -> Transition.POP."""
```

`ui/search_prompt.py`:
```python
class SearchValuePrompt(View):
    def __init__(self, table: str, column: str): ...
    def handle_key(self, key: int) -> Transition | None:
        """Printable chars append to buffer; RETURN with empty buffer is a no-op
        (FR7); RETURN with non-empty buffer -> Transition.PUSH(outcome_view)
        after calling find_matches; ESCAPE -> Transition.POP."""
```

`ui/match_list.py`:
```python
class MatchListView(View):
    def __init__(self, table: str, records: list[dict[str, object]]): ...
    def handle_key(self, key: int) -> Transition | None:
        """UP/DOWN move highlight, scrolling as needed; RETURN ->
        Transition.PUSH(<EP-3 table view for highlighted record>);
        ESCAPE -> Transition.POP (back to pre-search view)."""
```

Main loop key routing (`cli.py`/`ui/app.py`): `if key == ord('s'): view_stack.reset_to(SearchSelectionDialog(pairs))` checked before `view_stack.current.handle_key(key)`.

## 6. Implementation plan (TDD)

### T1. Searchable pairs list + startup ordering       (closes: FR1, FR2, NFR1, AC1, AC2)
- Failing tests to write first:
  - `test_search_selection_dialog_lists_all_searchable_pairs`
  - `test_search_selection_dialog_entry_shows_table_and_column`
  - `test_table_with_no_search_columns_contributes_no_entries`
  - `test_run_ui_pushes_search_selection_dialog_before_any_other_view`
- Production code to make them pass:
  - `ui/search_dialog.py::SearchSelectionDialog.__init__` (built from `config.searchable_pairs()`)
  - `cli.py::run_ui` wiring: build `ViewStack`, push `SearchSelectionDialog` first

### T2. Selection dialog navigation and confirm/cancel       (closes: FR3, FR4, FR5, AC3, AC4, AC5)
- Failing tests to write first:
  - `test_down_moves_highlight_to_next_pair`
  - `test_up_moves_highlight_to_previous_pair`
  - `test_return_on_highlighted_pair_pushes_value_prompt_labeled_correctly`
  - `test_escape_pops_selection_dialog_without_pushing`
- Production code to make them pass:
  - `ui/search_dialog.py::SearchSelectionDialog.handle_key`

### T3. Value prompt entry, empty rejection, cancel       (closes: FR6, FR7, FR9, AC6, AC7, AC8)
- Failing tests to write first:
  - `test_value_prompt_appends_typed_characters_to_buffer`
  - `test_return_with_empty_buffer_is_rejected_no_transition`
  - `test_return_with_nonempty_buffer_triggers_lookup`
  - `test_escape_in_value_prompt_pops_to_selection_dialog_no_lookup`
- Production code to make them pass:
  - `ui/search_prompt.py::SearchValuePrompt.handle_key`

### T4. Match-outcome branching (lookup)       (closes: FR8, FR10, FR11, FR12, AC6, AC9, AC10, AC11)
- Failing tests to write first:
  - `test_find_matches_returns_single_match_for_one_row`
  - `test_find_matches_returns_multiple_matches_for_several_rows`
  - `test_find_matches_returns_no_match_naming_table_column_value`
  - `test_find_matches_uses_exact_match_not_substring`
- Production code to make them pass:
  - `search/lookup.py::find_matches`
  - `search/models.py::SearchOutcome` hierarchy

### T5. Reopening via `s` from anywhere, mid-entry discard       (closes: FR17, FR18, FR19, NFR2, AC12, AC13, AC14)
- Failing tests to write first:
  - `test_s_key_opens_selection_dialog_when_on_an_arbitrary_view`
  - `test_reopened_dialog_lists_same_pairs_highlight_on_first`
  - `test_s_key_mid_entry_in_value_prompt_discards_buffer`
- Production code to make them pass:
  - main-loop `s` interception (`ui/app.py` or equivalent, wired from `cli.py::run_ui`)

### T6. Match list rendering and navigation       (closes: FR13, FR14, FR15, FR16, AC15, AC16, AC17, AC18)
- Failing tests to write first:
  - `test_match_list_row_shows_every_configured_column_and_value`
  - `test_down_up_move_highlight_scrolling_with_no_match_count_limit`
  - `test_return_on_highlighted_match_pushes_that_records_table_view`
  - `test_escape_pops_match_list_to_pre_search_view`
- Production code to make them pass:
  - `ui/match_list.py::MatchListView`

### Refactor step (after T6)
- Once all views are green, check `SearchSelectionDialog` and `MatchListView` for duplicated Up/Down-highlight-with-scroll logic; if the same highlight/scroll arithmetic appears in both, extract a small `ui/scrollable_list.py` helper. Do not pre-extract before both exist.

## 7. Non-functional concerns

- **Startup ordering (NFR1):** enforced the same way as EP-1's NFR1 — an integration test asserts `run_ui` never renders anything before the first `SearchSelectionDialog` frame is on the stack.
- **Global `s` availability (NFR2):** covered by T5's tests driving `s` from a non-search view (a stub view pushed onto the stack) to confirm interception happens at the main-loop level, not per-view.
- **Terminal portability:** curses requires a real TTY; headless test runs use curses' `initscr`-free unit tests against `View.handle_key`/`render` directly (no real terminal), reserving actual `curses.wrapper` execution for a manual smoke test, consistent with EP-1's integration-test-via-patching style.

## 8. Risks & mitigations

- Risk: Epic 3 and Epic 5's specs independently confirmed `curses`, but Epic 4's spec recommended `prompt_toolkit` instead — a cross-epic conflict, since all four epics must share one TUI foundation. Mitigation: not this epic's to resolve alone; needs reconciling (e.g. via `/brainstorm 4 spec`) before implementation starts, since three of four epics already agree on `curses`.
- Risk: curses' terminal-dependent behavior makes some tests hard to automate headlessly. Mitigation: keep all `View.handle_key`/state logic curses-agnostic (plain Python taking an `int` keycode), so only rendering (`render(screen)`) touches curses APIs and everything else is unit-testable without a terminal.
- Risk: `s`-interception logic could accidentally swallow `s` when the operator is typing a search value that itself needs the letter "s". Mitigation: the value prompt (T3) must consume all printable characters into its buffer *before* the main loop's `s` check is reached — the main loop only intercepts `s` when the current view's `handle_key` does not itself claim the key (i.e., text-entry views declare themselves as consuming all printable input, so `s` interception is disabled while a value prompt has focus, per PRD journey 6.6 where `s` *does* still reopen even mid-entry — confirmed as intended by AC14, not a bug).

## 9. Open architecture decisions

_None — D1 was resolved in Cycle 1; see §10 Decision log. §3's Key architecture decisions already reflect it._

**D1 (resolved):** Which terminal UI foundation should the modal dialogs and key handling be built on? → `curses` (Python stdlib), per Cycle 1. *(Architecture advisor: no new runtime dependency, and manual window control is the most direct way to reproduce the PRD's literal box-drawing mockups and a simple global-key-interception loop across nested modals, matching the project's stdlib-first style so far.)*

## 10. Decision log

### Cycle 1 — answered
| #  | Question | Decision |
| -- | -------- | -------- |
| D1 | Which terminal UI foundation should the modal dialogs and key handling be built on? | `curses` (Python stdlib) |
