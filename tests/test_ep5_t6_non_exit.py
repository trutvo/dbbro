from dbbro.ui.app import dispatch_key
from dbbro.ui.errors import RelationLookupFailedError, SearchFailedError
from dbbro.ui.modals import ErrorNotice
from dbbro.ui.view_stack import ViewStack


class _ScriptedView:
    def __init__(self, errors):
        self._errors = list(errors)

    def render(self, screen):
        pass

    def handle_key(self, key):
        raise self._errors.pop(0)


def test_multiple_consecutive_search_failures_never_exit_the_main_loop():
    view = _ScriptedView([SearchFailedError() for _ in range(5)])
    stack = ViewStack(view)

    for _ in range(5):
        result = dispatch_key(stack, key=0)
        assert isinstance(result, ErrorNotice)


def test_mixed_search_and_relation_failures_never_exit_the_main_loop():
    view = _ScriptedView(
        [SearchFailedError(), RelationLookupFailedError(), SearchFailedError()]
    )
    stack = ViewStack(view)

    for _ in range(3):
        result = dispatch_key(stack, key=0)
        assert isinstance(result, ErrorNotice)
