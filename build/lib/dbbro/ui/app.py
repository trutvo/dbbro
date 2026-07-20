import curses

from ..config.models import Config
from ..history.history import History
from ..navigation.breadcrumb import Breadcrumb
from . import keys
from .errors import OperationFailedError
from .modals import ErrorNotice
from .search_dialog import SearchSelectionDialog
from .view_stack import ViewStack


def build_view_stack(
    config: Config, conn=None, breadcrumb: Breadcrumb = None, history: History = None
) -> ViewStack:
    return ViewStack(
        SearchSelectionDialog(
            config.searchable_pairs(),
            conn=conn,
            config=config,
            breadcrumb=breadcrumb,
            history=history,
        )
    )


def consumes_navigation_keys(view) -> bool:
    """True if `view` itself handles LEFT/RIGHT (e.g. cursor movement in a
    typed buffer). Views that don't define this default to False."""
    return getattr(view, "consumes_navigation_keys", lambda: False)()


def handle_navigation_keys(key: int, stack: ViewStack, history: History) -> None:
    """Only acts on LEFT/RIGHT when the current view does not itself claim
    them. Calls history.go_back()/go_forward() and, if a non-None entry
    comes back, redisplays that entry's already-built view without
    repeating any search or relation lookup (NFR1)."""
    entry = history.go_back() if key == keys.LEFT else history.go_forward()
    if entry is not None:
        stack.frames[-1] = entry.view


def dispatch_key(stack: ViewStack, key: int) -> ErrorNotice | None:
    """Calls stack.current.handle_key(key). On a returned Transition, applies
    it to the stack and returns None. On OperationFailedError, leaves the
    stack untouched (preserving the current view's state, FR11/FR12/NFR3)
    and returns a fresh ErrorNotice for the main loop to show."""
    try:
        transition = stack.current.handle_key(key)
    except OperationFailedError as err:
        return ErrorNotice(str(err))
    stack.apply(transition)
    return None


def render_frame(stdscr, stack: ViewStack, pending_modal: ErrorNotice | None) -> None:
    """Erases the screen once, then renders the current view (and the
    pending modal, if any) on top — the single mechanism that guarantees
    no screen ever shows stale content from a previously active view
    (FR13/AC13)."""
    stdscr.erase()
    stack.current.render(stdscr)
    if pending_modal is not None:
        pending_modal.render(stdscr)


def run(stdscr, config: Config, conn) -> None:
    """Curses main loop: builds the ViewStack, pushes the search selection
    dialog first (NFR1), then dispatches one key at a time. `s` and
    Left/Right are intercepted here, before the current view sees them, so
    reopening search / navigating history works regardless of what view is
    on top (FR17/NFR2) — except while a text-entry view (one whose
    consumes_navigation_keys() returns True, e.g. SearchValuePrompt) is on
    top, in which case `s`, Left, and Right are all handed to the view
    itself instead (so `s` can be typed as an ordinary character, and
    Left/Right move the text cursor). Once that view is popped or replaced
    (Return submits, Escape cancels), `s`/Left/Right are global again. A failed
    search or relation lookup raises OperationFailedError from within the
    current view's handle_key; dispatch_key catches it into a pending
    modal shown on top of, but never pushed onto, the view stack, so
    dismissing it (Return only) never creates a history entry (FR13/AC8).
    A terminal resize (KEY_RESIZE) just triggers curses.update_lines_cols()
    and a re-render — every draw call reads the terminal's current size
    fresh, so nothing else needs to change (FR14/NFR3)."""
    breadcrumb = Breadcrumb()
    history = History()
    stack = build_view_stack(config, conn=conn, breadcrumb=breadcrumb, history=history)
    pending_modal: ErrorNotice | None = None
    render_frame(stdscr, stack, pending_modal)

    while True:
        key = stdscr.getch()
        if key == curses.KEY_RESIZE:
            curses.update_lines_cols()
        elif pending_modal is not None:
            if pending_modal.handle_key(key):
                pending_modal = None
        elif key == keys.S and not consumes_navigation_keys(stack.current):
            stack.reset_to(
                SearchSelectionDialog(
                    config.searchable_pairs(),
                    conn=conn,
                    config=config,
                    breadcrumb=breadcrumb,
                    history=history,
                )
            )
        elif key in (keys.LEFT, keys.RIGHT) and not consumes_navigation_keys(
            stack.current
        ):
            handle_navigation_keys(key, stack, history)
        else:
            pending_modal = dispatch_key(stack, key)
        render_frame(stdscr, stack, pending_modal)
