# Epic 4 — Browsing History — Technical Specification

Tech spec for `4_browsing_history.md`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~92% after revision 2 — D1–D4 are resolved and reconciled onto Epic 2's actual `curses`/`ViewStack` foundation (superseding this spec's original `prompt_toolkit` proposal), and the `History` module remains fully TDD-planned and testable in isolation. The remaining gap: this spec introduces `consumes_navigation_keys()` as an addition to Epic 2's `View` protocol, but Epic 2's own spec doesn't yet define that method — it needs a small follow-up edit to `2_record_search-spec.md` to keep the two documents fully in sync.

## 1. Overview

This spec covers the session-only browsing history that lets an operator move backward/forward through previously displayed table views using Left/Right, without re-querying the database. This spec was first written before Epics 2 (Record Search) and 3 (Entry Table View) had their own tech specs, so it originally proposed `prompt_toolkit` as the shared TUI foundation; Epics 2, 3, and 5 have since independently settled on stdlib `curses` plus a pushable/poppable `ViewStack` of `View` objects (see `2_record_search-spec.md`'s §3/§4). This revision reconciles Epic 4 onto that same foundation rather than introducing a second UI stack. Out of scope: the content/layout of a table view itself (EP-3), how a record is matched (EP-2), error dialogs (EP-5), and any persistence of history across restarts. See `4_browsing_history.md`.

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| FR1 | New history entry on every table view display | §3, §6 T3 |
| FR2 | Opening search dialog does not create an entry | §3, §6 T3 (integration boundary) |
| FR3 | Entering/submitting a search value does not itself create an entry | §3, §6 T3 |
| FR4 | Left moves to preceding entry and displays it | §5, §6 T2 |
| FR5 | Left at earliest entry is a no-op | §5, §6 T1 |
| FR6 | Right moves to following entry and displays it | §5, §6 T2 |
| FR7 | Right at most-recent entry is a no-op | §5, §6 T1 |
| FR8 | Left/Right operate on one sequence regardless of search vs. relation origin | §3, §6 T3 |
| FR9 | Currently displayed view is always the current position's entry | §4, §6 T1 |
| FR10 | Every display adds a new entry, even exact revisits/cycles | §4, §6 T1 |
| FR11 | New entry from a non-latest position truncates forward entries first | §4, §6 T1 |
| FR12 | History never persists across restarts | §3, §4 |
| FR13 | No fixed size limit | §4, §6 T1 |
| FR14 | Left/Right move text cursor while typing in search input, else navigate history | §3 (D3), §6 T4 |
| FR15 | No visible feedback beyond leaving the view unchanged on no-op | §5, §6 T1 |
| FR16 | No explicit position indicator (counter/breadcrumb/list) exposed by this epic | §3, §7 |
| NFR1 | Back/forward re-display without repeating a search or relation lookup | §3 (D2), §4, §6 T1 |
| NFR2 | Left/Right available at any point on a table view, except while typing | §3, §6 T4 |
| NFR3 | History is session-scoped only, no persistent storage | §3, §4 |
| AC1 | Search result display → new entry | §6 T3 |
| AC2 | Relation-follow display → new entry | §6 T3 |
| AC3 | Opening search dialog without submitting → no entry | §6 T3 |
| AC4 | Submitted search with no resulting view → no entry | §6 T3 |
| AC5 | Left displays prior view when >1 visited | §6 T2 |
| AC6 | Left at earliest entry leaves view unchanged | §6 T1 |
| AC7 | Right after a Left displays the view left via that Left | §6 T2 |
| AC8 | Right at most-recent entry leaves view unchanged | §6 T1 |
| AC9 | New entry after moving back discards existing forward entries | §6 T1 |
| AC10 | Revisiting a recorded view adds a new entry, not reuse | §6 T1 |
| AC11 | Current view is itself the entry the position points to | §6 T1 |
| AC12 | Boundary Left/Right produce no popup/indicator/sound | §6 T1 |
| AC13 | Typing in search value input: Left/Right move cursor, not history | §6 T4 |
| AC14 | Restart → new session's history is empty | §6 T1 (construction test) |
| AC15 | No counter/breadcrumb/list of visited views shown by this epic | §7 |

## 3. Architecture

```
dbbro/
  config/                  # unchanged (EP-1)
  history/
    __init__.py
    models.py               # TableViewSnapshot, HistoryEntry (frozen dataclasses)
    history.py               # History: pure stack-with-pointer, no UI/DB knowledge
  ui/                        # shared foundation from Epic 2's spec (curses + ViewStack)
    view_stack.py            # ViewStack, View, Transition — defined by Epic 2, reused here
    keys.py                  # adds LEFT/RIGHT constants alongside Epic 2's UP/DOWN/RETURN/ESCAPE/'s'
  cli.py                     # run_ui(config) — main loop from Epic 2's spec, extended with Left/Right routing
```

Flow: whichever view in EP-2/EP-3 produces a table view (a successful search, or following a relation) calls `history.add_entry(snapshot)` with a `TableViewSnapshot` built from the already-rendered data, then renders it. `history.add_entry` truncates any entries beyond the current position first (FR11), appends the new entry, and moves the current position to it. Left/Right routing reuses Epic 2's main-loop dispatch pattern (the same one that intercepts `s`): the main loop first offers the key to `view_stack.current.handle_key(key)`; a text-entry view such as `SearchValuePrompt` consumes LEFT/RIGHT itself (moving its cursor within the typed buffer) and returns `Transition.NONE` to signal "handled, stay put" — this epic adds one narrow extension to Epic 2's `View` protocol, `consumes_navigation_keys() -> bool`, which text-input views override to return `True` so the main loop knows not to also treat LEFT/RIGHT as history navigation while typing. Only when the current view does not claim navigation keys does the main loop call `history.go_back()` / `history.go_forward()` and, if a non-`None` entry comes back, push/replace the displayed view with `entry.snapshot`'s rendering. `History` itself never imports or calls into `ui/`, EP-2, or EP-3 — it is a pure, standalone module tested with plain data.

**Key architecture decisions:**

- **stdlib `curses` plus Epic 2's `ViewStack`/`View`/`Transition` is the TUI foundation (D1, revised)** — Epics 2, 3, and 5 independently settled on this after this spec's first revision proposed `prompt_toolkit`; reconciled here so all four epics share one foundation rather than two competing ones. No new dependency beyond what Epic 2 already introduced.
- **A history entry stores a fully-resolved, immutable snapshot of the table view (D2)**, not an identifier or a callback — this is the only shape that satisfies NFR1's "without requiring the operator to repeat a search or relation lookup" by construction, since re-fetching or re-running EP-2/EP-3 logic on Left/Right would silently reintroduce a lookup.
- **Left/Right routing uses view-first key dispatch (D3, revised)**: reusing Epic 2's existing "current view gets first refusal" pattern (the same mechanism that lets a `SearchValuePrompt` consume printable characters before the main loop's `s`-interception check) rather than a prompt_toolkit-specific focus/bubbling model. A minimal `consumes_navigation_keys() -> bool` addition to the `View` protocol lets any text-entry view opt in without Epic 4 knowing that view's internals.
- **`History` is a pure, callback-free stack-with-pointer (D4)**: `add_entry`, `go_back`, `go_forward` all just return data; the main loop (`cli.py`) is the single place that reacts to their return values by re-rendering. This mirrors `dbbro/config/`'s existing pattern of pure modules composed by a thin orchestrator (`config/api.py`), keeps `History` independently unit-testable with no mocks, and avoids an injected-callback or pub-sub mechanism this single-listener use case doesn't need.
- **History is constructed fresh per process, held only in memory** (FR12/NFR3) — no file, cache, or serialization path exists for it; a new `History()` object is created each time `run_ui` starts.

## 4. Data model

`history/models.py` (frozen dataclasses, following `config/models.py`'s immutability convention):

- `TableViewSnapshot`: `table_name: str`, `fields: tuple[FieldSnapshot, ...]` — the fully-resolved, already-formatted rendering data for one table view at the moment it was displayed (column name, display value, whether it's a relation field, relation label if any). Built by EP-3's rendering code and handed to `history.add_entry()` as an opaque value; `History` never inspects its contents.
  - `FieldSnapshot`: `column: str`, `display_value: str`, `is_relation: bool`, `relation_label: str | None`.
- `HistoryEntry`: `snapshot: TableViewSnapshot` — a thin wrapper reserved for any future per-entry metadata (kept separate from `TableViewSnapshot` so EP-3's rendering shape can evolve without changing `History`'s own contract).

`history/history.py`:
- `History`: holds `_entries: list[HistoryEntry]` and `_position: int` (index into `_entries`, or `-1` when empty). Both are private/internal state; nothing outside the class mutates them directly.

Lifecycle: empty on construction (`_entries == []`, `_position == -1`) → `add_entry` always appends after truncating anything past `_position`, then sets `_position` to the new last index → `go_back`/`go_forward` only move `_position` within existing bounds, never mutate `_entries`.

## 5. API / interfaces

`history/history.py`:
```python
class History:
    def __init__(self) -> None:
        """Start empty; a new session always begins with no entries (FR12/AC14)."""

    def add_entry(self, snapshot: TableViewSnapshot) -> HistoryEntry:
        """Discard any entries after the current position (FR11/AC9), append a new
        entry wrapping `snapshot`, move the current position to it, and return it.
        Always adds a new entry, even for an exact revisit (FR10/AC10)."""

    def go_back(self) -> HistoryEntry | None:
        """Move the current position one entry earlier and return that entry.
        Returns None and leaves the position unchanged if already at the
        earliest entry (FR5/AC6) — the caller must treat None as a silent
        no-op with no feedback (FR15/AC12)."""

    def go_forward(self) -> HistoryEntry | None:
        """Symmetric to go_back: moves one entry later, or returns None at the
        most recent entry (FR7/AC8)."""

    def current(self) -> HistoryEntry | None:
        """Returns the entry at the current position, or None if history is
        empty (used by tests and by the controller to assert invariants;
        FR9/AC11)."""
```

`ui/view_stack.py` (extends Epic 2's `View` protocol; not owned by `History`):
```python
class View(Protocol):
    def render(self, screen) -> None: ...
    def handle_key(self, key: int) -> "Transition | None": ...
    def consumes_navigation_keys(self) -> bool:
        """Return True if this view itself handles LEFT/RIGHT (e.g. a text-entry
        view moving its cursor), so the main loop must not also treat them as
        history navigation. Default False for any view that doesn't override it."""
```

`cli.py` main-loop addition (alongside Epic 2's existing `s`-interception check):
```python
def handle_navigation_keys(key: int, view_stack: ViewStack, history: History) -> None:
    """Called after view_stack.current.handle_key(key); only acts on LEFT/RIGHT
    when view_stack.current.consumes_navigation_keys() is False. Calls
    history.go_back()/go_forward() and, if a non-None entry comes back,
    re-renders that entry's snapshot as the current view."""
```

Cross-epic contract this spec fixes for EP-2/EP-3 to build against:
- Whatever view in EP-2/EP-3 displays a table view must call `history.add_entry(snapshot)` immediately before/alongside rendering that same view — never on dialog-open or value-entry alone (FR2/FR3/AC3/AC4).
- The search-value prompt view must override `consumes_navigation_keys()` to return `True` while it holds an in-progress buffer, and must itself handle LEFT/RIGHT as cursor movement within that buffer, so those keys never reach the main loop's history handler while typing (FR14/AC13).

## 6. Implementation plan (TDD)

### T1. Pure `History` stack-with-pointer            (closes: FR1, FR9, FR10, FR11, FR12, FR13, FR15, NFR3, AC6, AC8, AC9, AC10, AC11, AC12, AC14)
- Failing tests to write first:
  - `test_new_history_is_empty_and_current_is_none`
  - `test_add_entry_appends_and_becomes_current`
  - `test_add_entry_always_adds_even_for_identical_snapshot` (revisit/cycle case)
  - `test_add_entry_after_go_back_truncates_forward_entries`
  - `test_go_back_at_earliest_entry_returns_none_and_position_unchanged`
  - `test_go_forward_at_latest_entry_returns_none_and_position_unchanged`
  - `test_history_has_no_size_limit` (add many entries, all retained)
- Production code to make them pass:
  - `history/models.py::TableViewSnapshot`, `FieldSnapshot`, `HistoryEntry`
  - `history/history.py::History` (`add_entry`, `go_back`, `go_forward`, `current`)

### T2. Back/forward re-display sequencing            (closes: FR4, FR6, AC5, AC7)
- Failing tests to write first:
  - `test_go_back_then_go_forward_returns_to_the_entry_left_via_back` (multi-step: add 3 entries, back twice, forward once, assert entry matches the one left)
  - `test_go_back_returns_the_entry_immediately_preceding_current`
- Production code to make them pass:
  - No new production code beyond T1 if `History`'s pointer arithmetic is correct; this task is a dedicated sequencing test pass validating the contract EP-3's renderer will rely on.

### T3. Cross-epic recording contract              (closes: FR1, FR2, FR3, FR8, NFR1, AC1, AC2, AC3, AC4)
- Failing tests to write first:
  - `test_add_entry_called_on_search_result_display` (fake controller: simulate EP-2 producing a snapshot, assert `history.add_entry` was called exactly once)
  - `test_add_entry_called_on_relation_follow_display` (same, simulating EP-3's relation navigation)
  - `test_opening_search_dialog_alone_does_not_call_add_entry`
  - `test_submitting_search_value_without_a_resulting_view_does_not_call_add_entry`
  - `test_go_back_does_not_trigger_any_lookup_or_query` (assert a stub "DB lookup" spy is never invoked during go_back/go_forward, proving NFR1)
- Production code to make them pass:
  - `ui/app.py::build_application(config)` wiring: a single `on_table_view_displayed(snapshot)` hook, called by EP-2/EP-3 controller code (stubbed with a fake in this epic's own tests, since EP-2/EP-3 aren't implemented yet), which calls `history.add_entry` then `renderer.show`.

### T4. Left/Right key routing incl. text-input precedence    (closes: FR14, NFR2, AC13)
- Failing tests to write first:
  - `test_left_right_navigate_history_when_current_view_does_not_consume_navigation_keys` (stub `View` with `consumes_navigation_keys() -> False`)
  - `test_left_right_move_cursor_when_search_prompt_view_consumes_navigation_keys` (stub/real `SearchValuePrompt`-like view with `consumes_navigation_keys() -> True`; assert `history.go_back`/`go_forward` are never called)
  - `test_left_right_navigate_history_immediately_after_search_prompt_view_is_popped`
- Production code to make them pass:
  - `ui/view_stack.py::View.consumes_navigation_keys` (default `False`)
  - `cli.py::handle_navigation_keys`, wired into the main loop after Epic 2's `s`-interception check
  - The search-value prompt view overriding `consumes_navigation_keys()` to `True` and handling LEFT/RIGHT as cursor movement within its own buffer (minimal stub sufficient for this epic; the full search dialog is EP-2's responsibility)

### Refactor step (after T4)
- Once all tests are green, review `ui/app.py` for any duplicated "call history then call renderer" logic between the search-result path and the relation-follow path from T3; if EP-2/EP-3 later introduce a third display trigger (e.g. match-list selection), extract a single `display_table_view(snapshot)` helper rather than repeating the two-call sequence a third time.

## 7. Non-functional concerns

- **Left/Right precedence while typing (NFR2/FR14):** enforced structurally — the main loop only calls `history.go_back`/`go_forward` when `view_stack.current.consumes_navigation_keys()` is `False`; a text-entry view returning `True` makes it structurally impossible for LEFT/RIGHT to reach history navigation while that view is on top of the stack.
- **No re-query on navigation (NFR1):** enforced by T3's spy-based test — `go_back`/`go_forward` must never call anything resembling a DB/record lookup; this is structurally guaranteed by `History` never holding a reference to any lookup function, only opaque snapshots.
- **Session scope only (NFR3/FR12):** `History` has no file I/O, no serialization method, and is constructed fresh in `run_ui`; there is nothing to disable for "no persistence" because no persistence path is ever written.
- **No exposed position indicator (FR16/AC15):** the renderer's `show(snapshot)` call is given exactly the same `TableViewSnapshot` shape whether reached by search, relation-follow, or history navigation — there is no separate "history mode" render path that could accidentally add a counter or breadcrumb.
- **Unbounded growth (FR13):** `_entries` is a plain `list`; no eviction or capping logic is introduced. Documented as an accepted memory trade-off for a console app's session lifetime (matches PRD's explicit no-limit requirement).

## 8. Risks & mitigations

- Risk: this spec's `TableViewSnapshot` shape was designed before Epic 3 had its own spec, so it's effectively a binding decision made on Epic 3's behalf. Mitigation: `TableViewSnapshot`'s field list is minimal and additive (a tuple of simple value fields), so Epic 3's spec (`3_entry_table_view-spec.md`) can extend it without breaking `History`'s contract.
- Risk: `consumes_navigation_keys()` is a new addition to Epic 2's `View` protocol proposed by this spec, not present in Epic 2's own spec as written. Mitigation: it's a minimal, additive, default-`False` method — Epic 2's existing views (`SearchSelectionDialog`, `MatchListView`) need no change; only `SearchValuePrompt` must override it. Flag this addition to Epic 2's maintainers so its spec absorbs the same method rather than diverging.
- Risk: storing a full resolved snapshot per entry could become a real memory concern for very long sessions with wide tables. Mitigation: out of scope per PRD's explicit "no size limit" requirement (Q2 in the PRD's decision log); revisit only if it becomes an observed problem.

## 9. Open architecture decisions

_None — D1–D4 were resolved in Cycle 1; see §10 Decision log. §3–§7 already reflect all four._

**D1 (resolved, revised):** Which TUI/input-handling library does the whole app (and this epic's key router) build on? → stdlib `curses`, per Cycle 1 — the user overrode this spec's original `prompt_toolkit` recommendation, aligning Epic 4 with Epics 2, 3, and 5, which had all independently settled on `curses` by the time this cycle ran.

**D2 (resolved):** What does a history entry store to satisfy "no repeated lookup" on Left/Right? → A fully-resolved, immutable rendered snapshot captured at display time, per Cycle 1. *(Architecture advisor: this is the only shape that guarantees NFR1's "without requiring the operator to repeat a search or relation lookup" by construction, since the alternatives either explicitly re-query or defer to EP-2/EP-3 logic that may itself re-query.)*

**D3 (resolved, revised):** How does the Left/Right key router know when the operator is typing in the search input, without owning EP-2's internals? → View-first key dispatch, per Cycle 1 — re-expressed against Epic 2's `ViewStack`/`View.handle_key` model (a new `consumes_navigation_keys()` method on `View`) rather than prompt_toolkit's focus/bubbling system, since D1 was revised to `curses`. *(Architecture advisor: the original rationale — zero cross-epic enum/flag contract, the input view simply claims the keys it needs — holds regardless of which UI toolkit implements the dispatch.)*

**D4 (resolved):** How is `History` wired to whatever renders a table view on screen? → `History` is pure data; the main loop explicitly re-renders after every `add_entry`/`go_back`/`go_forward`, per Cycle 1. *(Architecture advisor: mirrors `config/`'s existing pure-module-plus-thin-orchestrator pattern, keeps `History` mock-free and independently unit-testable, and avoids overengineering for a single-listener use case.)*

## 10. Decision log

### Cycle 1 — answered
| #  | Question | Decision |
| -- | -------- | -------- |
| D1 | Which TUI/input-handling library does the whole app build on? | stdlib `curses` (overriding this spec's original `prompt_toolkit` recommendation, to align with Epics 2/3/5) |
| D2 | What does a history entry store? | A fully-resolved, immutable rendered snapshot captured at display time |
| D3 | How does the Left/Right router know when the operator is typing? | View-first key dispatch via a `consumes_navigation_keys()` addition to Epic 2's `View` protocol |
| D4 | How is `History` wired to the renderer? | `History` is pure data; the main loop calls it and re-renders explicitly |
