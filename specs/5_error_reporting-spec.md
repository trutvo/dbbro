# Epic 5 — Error Reporting — Technical Specification

Tech spec for `5_error_reporting.md`. Implementation-level decisions live here; product requirements stay in the PRD.

> **Confidence:** ~95% after revision 3 — D1–D3 are all resolved; this epic now reuses Epic 2's `View`/`Transition`/`ViewStack` verbatim instead of a competing sketch, and the `dispatch_operation`/`attempt_id` machinery was simplified away once reconciliation showed FR7's modality already rules out any supersession race. The remaining minor gap is that Epic 2's own spec doesn't yet mention `OperationFailedError`/the `dispatch_key` wrapping — a small follow-up note there would make the pair fully symmetric, though nothing in this spec depends on that edit happening first.

## 1. Overview

This spec covers the error-notice modal and the failure-signaling mechanism that surfaces it: detecting that a search (EP-2) or relation lookup (EP-3) failed, showing a modal dialog describing which operation failed, and — on Return — dismissing it and restoring the operator's exact previous view/dialog state unchanged. Out of scope: the search and relation-lookup logic themselves (EP-2/EP-3), configuration-loading errors (EP-1, already handled via `ConfigValidationError`), and any change to successful search/lookup behavior. See `5_error_reporting.md`.

This spec was first written before Epics 2-4 had tech specs. Epic 2 has since published `2_record_search-spec.md`, which defines the actual shared `dbbro/ui/view_stack.py` foundation (`View`, `Transition`, `ViewStack`) that Epics 3 and 4 already build on. This revision adopts that foundation verbatim rather than the independent `View`/`app.py` sketch this spec originally proposed — see D3 in §9/§10.

## 2. Requirements coverage

| PRD ref | Summary | Covered by |
| ------- | ------- | ---------- |
| FR1  | Error notice on failed/no-match search | §3, §6 T2, T3 |
| FR2  | Error notice on failed relation lookup | §3, §6 T2, T3 |
| FR3  | Notice states which operation failed, not the cause | §4, §6 T2 |
| FR4  | Only search/relation lookup trigger this mechanism | §3, §6 T2 |
| FR5  | Exactly one notice per failed operation | §3, §6 T3 |
| FR6  | New search submission supersedes earlier notice/outcome | §3, §6 T5 |
| FR7  | Notice is modal (blocks underlying view) | §5, §6 T1 |
| FR8  | Notice stays until dismissed, no auto-dismiss | §5, §6 T1 |
| FR9  | No search/relation failure ever exits dbbro | §3, §6 T3, T6 |
| FR10 | Return dismisses; only Return | §5, §6 T1 |
| FR11 | Dismissal restores exact previous view/dialog state | §3, §6 T4 |
| FR12 | Dismissal never alters the restored view's state | §3, §6 T4 |
| FR13 | Failed operation never advances browsing history | §3, §6 T4 |
| NFR1 | Notice appears immediately, no extra operator action | §3, §6 T3 |
| NFR2 | Description distinguishes search vs. relation-lookup failure | §4, §6 T2 |
| NFR3 | Repeated dismiss/retrigger never degrades view restoration | §3, §6 T4, T5 |
| NFR4 | dbbro never terminates on such a failure | §3, §6 T6 |
| AC1  | Unresolvable search value → notice, not empty/crashed view | §6 T3 |
| AC2  | Failed relation lookup → notice, not empty/crashed view | §6 T3 |
| AC3  | Underlying view not interactable while notice shown | §6 T1 |
| AC4  | Only Return closes notice, no timeout | §6 T1 |
| AC5  | Return closes the notice | §6 T1 |
| AC6  | Dismissed search failure → back to search dialog, selection + typed value intact | §6 T4 |
| AC7  | Dismissed relation-lookup failure → back to table view, same field selected | §6 T4 |
| AC8  | Dismissing notice adds no history entry | §6 T4 |
| AC9  | No-match search shown via same notice as any other failed search | §6 T2, T3 |
| AC10 | Exactly one notice, never combined | §6 T3 |
| AC11 | Dismiss → edit → resubmit shows only the new outcome | §6 T5 |
| AC12 | dbbro keeps running, shows dismissible notice, never exits | §6 T6 |

## 3. Architecture

```
dbbro/
  ui/
    __init__.py
    view_stack.py     # unchanged from Epic 2's spec: View, Transition, ViewStack
    errors.py         # OperationFailedError base, SearchFailedError, RelationLookupFailedError
    modals.py         # ErrorNotice: renders the double-line modal, handle_key only accepts Return
  config/            # unchanged (EP-1)
  cli.py             # run_ui(config): Epic 2's curses.wrapper main loop, extended with the
                      #   try/except OperationFailedError wrap described below
```

Flow: the operator's action (submitting a search value, pressing Return on a relation field) calls into EP-2/EP-3 lookup logic from inside the current `View`'s `handle_key`. That lookup logic raises `SearchFailedError` or `RelationLookupFailedError` — both subclasses of `OperationFailedError` — instead of returning a sentinel or a `Transition`. The main loop (Epic 2's `cli.py::run_ui`/`app_main`) wraps every `view_stack.current.handle_key(key)` call in `try/except OperationFailedError`; on success it applies the returned `Transition` to `view_stack` exactly as Epic 2 already specifies, and on `OperationFailedError` it does not apply any transition at all — `view_stack` is left completely untouched, so the current view (search dialog's selection + typed value, or table view's selected field) is preserved by construction, satisfying FR11/FR12/NFR3. The caught error is stored as an `ErrorNotice` in a single-slot `pending_modal` variable held by the main loop, outside `view_stack` entirely — never pushed onto it — which keeps FR13/AC8 (no history entry) automatically satisfied, since only `view_stack.push` calls are recorded as history by EP-4.

Each frame, the main loop renders `view_stack.current` first; if `pending_modal` is set, it renders the `ErrorNotice` on top and routes all key events to it instead of to `view_stack.current` (`ErrorNotice.handle_key` accepts only Return, ignoring all other keys, satisfying FR10/AC4/FR7). On Return, the main loop clears `pending_modal` and resumes normal `view_stack.current.handle_key` dispatch — no view transition ever occurred during the failure, so FR9/NFR4 hold because `OperationFailedError` is always caught before it can propagate out of the loop; nothing else the loop does raises `OperationFailedError`, so the `except` is exhaustive by construction for FR4.

Supersession (FR6/AC11) needs no extra bookkeeping: because `pending_modal` is a single slot and the notice is strictly modal (FR7 blocks every other key while it's showing), the operator can only ever act on the *current* pending modal — dismiss it via Return first, then edit and resubmit. That resubmission's `handle_key` call either succeeds (applying a `Transition`, leaving `pending_modal` unset) or raises again (overwriting `pending_modal` with the new notice); there is no reachable interleaving where a stale modal and a fresh one could coexist or race, so no generation/attempt-id tracking is needed. A no-match search result is normalized to raise `SearchFailedError` from the same lookup call site as a hard failure (AC9), so both share one code path into the modal.

**Key architecture decisions:**

- **Terminal rendering via the stdlib `curses` module (D1)** — matches the briefing's exact box-drawing character spec (single-line panels, double-line modals) without fighting a widget/CSS abstraction, and introduces no new dependency, consistent with Epic 1's dependency-light convention. *(Architecture advisor: curses renders the mandated glyphs literally and needs no fight against a competing widget/styling model, unlike prompt_toolkit/urwid/textual, while adding zero new dependency in keeping with dbbro/config/'s minimal-dependency style.)*
- **Failure signaling via typed exceptions, not Result values/events/polling (D2)** — `SearchFailedError`/`RelationLookupFailedError` subclass a common `OperationFailedError`, mirroring Epic 1's `ConfigValidationError` convention (a purpose-built exception carrying structured data, raised once, caught centrally) rather than introducing a second failure-handling idiom. *(Architecture advisor: extends the exact convention Epic 1 already established — one exception type, structured data, single catch point — giving exactly-one-notice-per-failure and leaving surrounding view state untouched by construction, with no new abstraction like an event bus.)*
- **This epic reuses Epic 2's `View`/`Transition`/`ViewStack` verbatim rather than a separate `dispatch_operation` wrapper (D3)** — the main loop itself wraps `view_stack.current.handle_key(key)` in `try/except OperationFailedError`, so `dbbro/ui/` has exactly one `View` contract shared by every epic, not two. *(Architecture advisor: Epic 2's `ViewStack`/`Transition` shape is already load-bearing for Epics 3 and 4, so Epic 5 is the one that should conform; the main loop is the natural place to wrap the existing `handle_key` call, since it already owns key-dispatch and outcome-mapping.)*
- **The error modal occupies a "pending modal" slot outside the view stack**, not a pushed `View` — the single most direct way to guarantee dismissal never creates a history entry (FR13/AC8) without EP-4's history code needing to know anything about errors at all.
- **`OperationFailedError` carries only an operation-kind marker (search vs. relation lookup), never the underlying cause** — mirrors FR3's requirement not to explain *why*, and keeps `ErrorNotice`'s rendering logic trivial (two fixed message templates).

## 4. Data model

`dbbro/ui/errors.py`:

```python
class OperationFailedError(Exception):
    """Base for a failed search or relation lookup; caught centrally by app.py."""

class SearchFailedError(OperationFailedError):
    def __str__(self) -> str:
        return "Search failed: no matching record was found."

class RelationLookupFailedError(OperationFailedError):
    def __str__(self) -> str:
        return "Could not follow relation: the related record could not be looked up."
```

Both are raised with no extra payload beyond the fixed message — satisfying FR3/NFR2 (distinguishes which operation failed, not the cause) without inventing wording the PRD deliberately leaves unconstrained (see PRD §11-adjacent note in the PRD's confidence line).

`dbbro/ui/modals.py`:

```python
@dataclass
class ErrorNotice:
    message: str        # str(the OperationFailedError instance)
```

No other new persisted entities; `ErrorNotice` is transient UI state held by the main loop's `pending_modal` variable, never written to the browsing history (EP-4) or anywhere durable — consistent with the PRD's "out of scope: logging/persisting error details." No generation/attempt-id field is needed (see §3's supersession note — modality alone rules out any race).

## 5. API / interfaces

`dbbro/ui/modals.py`:
```python
class ErrorNotice:
    def render(self, screen) -> None: ...
    def handle_key(self, key: int) -> bool:
        """Return True (dismissed) only when key is Return; otherwise ignore and return False."""
```

`dbbro/cli.py` (extends Epic 2's main-loop function, however it is named there — `run_ui`/`app_main`):
```python
def dispatch_key(view_stack: ViewStack, key: int) -> ErrorNotice | None:
    """Calls view_stack.current.handle_key(key). On a returned Transition, applies
    it to view_stack exactly as Epic 2 specifies and returns None. On
    OperationFailedError, leaves view_stack untouched and returns a fresh
    ErrorNotice(str(err)) for the main loop to store as pending_modal."""
```

`dbbro/cli.py`: `run_ui(config)` is Epic 2's existing curses main loop, with its per-key dispatch call replaced by `dispatch_key`, and one added branch: when `pending_modal` is set, render `ErrorNotice` and route keys to it instead of `view_stack.current` until Return clears it. This replaces the current `NotImplementedError` stub.

Interfaces EP-2/EP-3 must honor going forward (not implemented by this epic, but fixed by it):
- Search lookup and relation-lookup functions raise `SearchFailedError` / `RelationLookupFailedError` respectively on failure (including no-match, for search) instead of returning `None`/a sentinel, from within a `View.handle_key` implementation.
- No separate wrapper is required at call sites beyond the main loop's own `dispatch_key`; a `View.handle_key` may simply let the exception propagate out of its own body.

## 6. Implementation plan (TDD)

### T1. `ErrorNotice` modal: render + Return-only dismissal            (closes: FR7, FR8, FR10, AC3, AC4, AC5)
- Failing tests to write first:
  - `test_error_notice_handle_key_return_dismisses`
  - `test_error_notice_handle_key_other_keys_ignored` (parametrize over a sample of non-Return keys)
  - `test_error_notice_render_draws_modal_over_provided_screen` (asserts the double-line box chars appear, underlying view's render is not called while notice pending — covers AC3 at the `App` level in T2)
- Production code to make them pass:
  - `dbbro/ui/modals.py::ErrorNotice`

### T2. Failure exception types                                        (closes: FR3, FR4, NFR2)
- Failing tests to write first:
  - `test_search_failed_error_message_identifies_search`
  - `test_relation_lookup_failed_error_message_identifies_relation_lookup`
  - `test_error_messages_are_distinct_between_the_two_types`
- Production code to make them pass:
  - `dbbro/ui/errors.py::OperationFailedError`, `SearchFailedError`, `RelationLookupFailedError`

### T3. Main loop's `dispatch_key` catches failures into exactly one pending modal   (closes: FR1, FR2, FR5, FR9, NFR1, NFR4, AC1, AC2, AC9, AC10, AC12)
- Failing tests to write first:
  - `test_dispatch_key_sets_pending_modal_on_search_failed_error`
  - `test_dispatch_key_sets_pending_modal_on_relation_lookup_failed_error`
  - `test_dispatch_key_no_match_search_treated_as_search_failed` (a stub view's `handle_key` raises `SearchFailedError` for a no-match outcome; asserts identical modal path to a hard failure)
  - `test_dispatch_key_never_produces_more_than_one_pending_modal_per_call`
  - `test_dispatch_key_reraises_only_non_operation_failed_exceptions` (unexpected exceptions still propagate — dbbro doesn't silently swallow programmer errors — while confirming the main loop itself never exits on `OperationFailedError`)
  - `test_main_loop_survives_operation_failed_error_without_exiting` (integration-level: loop keeps iterating)
- Production code to make them pass:
  - `dbbro/cli.py::dispatch_key` (catch clause), main-loop's pending-modal render precedence

### T4. View restoration on dismissal, unaltered and history-free      (closes: FR11, FR12, FR13, NFR3, AC6, AC7, AC8)
- Failing tests to write first:
  - `test_dismiss_after_search_failure_restores_same_selection_and_typed_value`
  - `test_dismiss_after_relation_lookup_failure_restores_same_selected_field`
  - `test_dismiss_does_not_mutate_the_underlying_view_object` (identity/equality check on the view before vs. after)
  - `test_dismiss_does_not_push_a_history_entry` (view-stack/history length unchanged before vs. after the fail+dismiss cycle)
  - `test_repeated_fail_dismiss_cycles_still_restore_correctly` (covers NFR3: run the fail/dismiss loop 3+ times, assert no drift)
- Production code to make them pass:
  - `dbbro/cli.py`: `pending_modal` kept as a variable fully separate from `view_stack`; clearing it on Return never calls any `ViewStack` mutation method

### T5. Supersession on dismiss-then-resubmit                           (closes: FR6, AC11)
- Failing tests to write first:
  - `test_dismiss_then_resubmit_with_new_success_clears_pending_modal_and_applies_transition`
  - `test_dismiss_then_resubmit_with_new_failure_shows_only_the_new_notice`
- Production code to make them pass:
  - No new production code beyond T3/T4 — this task is a dedicated sequencing test proving the single-slot `pending_modal` design needs no generation/attempt tracking (see §3), since modality (FR7) rules out any interleaving where a stale and fresh notice could coexist

### T6. Non-exit guarantee under repeated/varied failures                (closes: FR9, NFR4, AC12)
- Failing tests to write first:
  - `test_multiple_consecutive_search_failures_never_exit_the_main_loop`
  - `test_mixed_search_and_relation_failures_never_exit_the_main_loop`
- Production code to make them pass:
  - Covered by the same `dispatch_key` catch clause from T3; this task is a dedicated regression pass exercising it under a mixed sequence of failures rather than new production code

### Refactor step (after T6)
- Once T1-T6 are green, review whether `SearchFailedError`/`RelationLookupFailedError`'s fixed `__str__` templates should move into `ErrorNotice` itself (so `errors.py` stays free of presentation strings) — defer this until EP-2/EP-3 show whether either exception needs to carry more than a marker.

## 7. Non-functional concerns

- **Immediacy (NFR1):** the modal is set synchronously inside `dispatch_key`, in the same call stack as the failing `handle_key` call — no polling, no deferred render, so it appears on the very next frame drawn.
- **Distinguishable messaging (NFR2):** `SearchFailedError` and `RelationLookupFailedError` have distinct fixed `__str__` values (see §4); a snapshot-style test (T2) pins both strings so they can't silently converge.
- **Restoration robustness (NFR3):** because `pending_modal` never touches `view_stack` (§3), there is no accumulating state to degrade across repeated cycles; T4's repeated-cycle test is the regression guard.
- **Never-exit guarantee (NFR4):** `OperationFailedError` is caught at exactly one point (`dispatch_key`), and nothing else in the loop raises it, so it can never reach the main loop's outer boundary uncaught; other exception types are intentionally allowed to propagate (T3's re-raise test) since crashing on a genuine programmer error is out of this epic's scope — only search/relation-lookup failures are covered.
- **No persistence:** per the PRD's out-of-scope note, `ErrorNotice`/`OperationFailedError` carry no logging or export hook; they exist only in the main loop's in-memory `pending_modal` variable for the duration of one dismiss cycle.

## 8. Risks & mitigations

- Risk: this spec's `View`/error-dispatch design originally predated Epic 2's now-published spec and used an incompatible `View.handle_key(key) -> None` plus a separate `App.dispatch_operation` wrapper. Mitigation: resolved (D3) — this revision adopts Epic 2's `View.handle_key(key) -> Transition | None` / `ViewStack` verbatim; the main loop's `dispatch_key` wraps that call in `try/except OperationFailedError` instead of introducing a parallel mechanism, so `dbbro/ui/` has exactly one `View` contract.
- Risk: normalizing "no-match search" to raise `SearchFailedError` from within EP-2's lookup code (rather than this epic's own code) means EP-2's spec must actually do that when it's written. Mitigation: called out explicitly in §5's "interfaces EP-2/EP-3 must honor," so it is visible before EP-2 implementation starts.
- Risk: curses-based rendering (D1) has known cross-platform quirks (notably limited/awkward Windows support). Mitigation: out of scope for this epic; flagged for whoever writes EP-2's spec, which will own the bulk of curses-based rendering code.

## 9. Open architecture decisions

_None — D1–D3 were resolved across Cycles 1–2; see §10 Decision log. §3, §5–§7 already reflect all three._

**D1 (resolved):** Terminal rendering / TUI approach → stdlib `curses`, per Cycle 1. *(Architecture advisor: curses renders the mandated glyphs literally and needs no fight against a competing widget/styling model, unlike prompt_toolkit/urwid/textual, while adding zero new dependency in keeping with dbbro/config/'s minimal-dependency style.)* Confirmed by Epics 2, 3, and 4's own specs, which independently settled on the same foundation.

**D2 (resolved):** Failure-signaling mechanism from search/relation-lookup code to the UI layer → typed exceptions (`SearchFailedError`/`RelationLookupFailedError` subclassing `OperationFailedError`), caught once in the main loop's `dispatch_key`, per Cycle 1. *(Architecture advisor: extends the exact convention Epic 1 already established — one exception type, structured data, single catch point — giving exactly-one-notice-per-failure and leaving surrounding view state untouched by construction, with no new abstraction like an event bus.)*

**D3 (resolved):** How should Epic 5's `View`/error-dispatch design converge with Epic 2's actual `ViewStack`/`Transition`/`View.handle_key` shapes? → Adopt Epic 2's `Transition`-returning `handle_key(key) -> Transition | None` verbatim; the main loop wraps each `view_stack.current.handle_key(key)` call in `try/except OperationFailedError`, replacing this spec's original separate `dispatch_operation` wrapper, per Cycle 2. *(Architecture advisor: Epic 2's `ViewStack`/`Transition` shape is already load-bearing for Epics 3 and 4, so Epic 5 is the one that should conform; the main loop is the natural place to wrap the existing `handle_key` call, since it already owns key-dispatch and outcome-mapping.)*

## 10. Decision log

### Cycle 1 — answered
| #  | Question | Decision |
| -- | -------- | -------- |
| D1 | Terminal rendering / TUI approach | stdlib `curses` |
| D2 | Failure-signaling mechanism from search/relation-lookup code to the UI layer | Typed exceptions (`OperationFailedError` subclasses), caught once centrally |

### Cycle 2 — answered
| #  | Question | Decision |
| -- | -------- | -------- |
| D3 | How should Epic 5's `View`/error-dispatch design converge with Epic 2's actual `ViewStack`/`Transition`/`View.handle_key` shapes? | Adopt Epic 2's `Transition`-returning `handle_key` verbatim; main loop wraps it in `try/except OperationFailedError`, no separate `dispatch_operation` wrapper |
