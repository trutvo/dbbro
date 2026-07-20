from dbbro.ui.app import dispatch_key
from dbbro.ui.errors import SearchFailedError
from dbbro.ui.view_stack import ViewStack


class _StatefulRaisingView:
    """Mimics a search prompt: mutates its own buffer, then fails the lookup."""

    def __init__(self):
        self.buffer = ""

    def render(self, screen):
        pass

    def handle_key(self, key):
        self.buffer += chr(key)
        raise SearchFailedError()


def test_dismiss_after_search_failure_restores_same_selection_and_typed_value():
    view = _StatefulRaisingView()
    stack = ViewStack(view)

    dispatch_key(stack, key=ord("x"))

    assert stack.current is view
    assert stack.current.buffer == "x"


def test_dismiss_does_not_mutate_the_underlying_view_object():
    view = _StatefulRaisingView()
    stack = ViewStack(view)

    dispatch_key(stack, key=ord("x"))

    assert stack.current is view


def test_dismiss_does_not_push_a_history_entry():
    view = _StatefulRaisingView()
    stack = ViewStack(view)

    dispatch_key(stack, key=ord("x"))

    assert stack.frames == [view]


def test_repeated_fail_dismiss_cycles_still_restore_correctly():
    view = _StatefulRaisingView()
    stack = ViewStack(view)

    for key in (ord("a"), ord("b"), ord("c")):
        dispatch_key(stack, key=key)

    assert stack.current is view
    assert stack.current.buffer == "abc"
    assert stack.frames == [view]
