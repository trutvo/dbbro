from dbbro.ui.app import dispatch_key
from dbbro.ui.errors import SearchFailedError
from dbbro.ui.modals import ErrorNotice
from dbbro.ui.view_stack import Transition, ViewStack


class _ScriptedView:
    """A stub view whose handle_key outcome is scripted per call."""

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)

    def render(self, screen):
        pass

    def handle_key(self, key):
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_dismiss_then_resubmit_with_new_success_clears_pending_modal_and_applies_transition():
    other = object()
    view = _ScriptedView([SearchFailedError(), Transition.push(other)])
    stack = ViewStack(view)

    first = dispatch_key(stack, key=0)
    assert isinstance(first, ErrorNotice)
    # operator dismisses (Return) before resubmitting — modeled by simply
    # calling dispatch_key again, since dismissal is orthogonal to the stack
    second = dispatch_key(stack, key=0)

    assert second is None
    assert stack.current is other


def test_dismiss_then_resubmit_with_new_failure_shows_only_the_new_notice():
    view = _ScriptedView([SearchFailedError(), SearchFailedError()])
    stack = ViewStack(view)

    first = dispatch_key(stack, key=0)
    second = dispatch_key(stack, key=0)

    assert isinstance(first, ErrorNotice)
    assert isinstance(second, ErrorNotice)
    assert stack.frames == [view]
