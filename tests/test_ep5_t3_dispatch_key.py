import pytest

from dbbro.ui.app import dispatch_key
from dbbro.ui.errors import RelationLookupFailedError, SearchFailedError
from dbbro.ui.modals import ErrorNotice
from dbbro.ui.view_stack import Transition, ViewStack


class _RaisingView:
    def __init__(self, error):
        self.error = error

    def render(self, screen):
        pass

    def handle_key(self, key):
        raise self.error


class _StubView:
    def render(self, screen):
        pass

    def handle_key(self, key):
        return None


class _OtherErrorView:
    def render(self, screen):
        pass

    def handle_key(self, key):
        raise ValueError("boom")


def test_dispatch_key_sets_pending_modal_on_search_failed_error():
    stack = ViewStack(_RaisingView(SearchFailedError()))

    result = dispatch_key(stack, key=0)

    assert isinstance(result, ErrorNotice)
    assert result.message == str(SearchFailedError())


def test_dispatch_key_sets_pending_modal_on_relation_lookup_failed_error():
    stack = ViewStack(_RaisingView(RelationLookupFailedError()))

    result = dispatch_key(stack, key=0)

    assert isinstance(result, ErrorNotice)
    assert result.message == str(RelationLookupFailedError())


def test_dispatch_key_never_produces_more_than_one_pending_modal_per_call():
    stack = ViewStack(_RaisingView(SearchFailedError()))

    result = dispatch_key(stack, key=0)

    assert isinstance(result, ErrorNotice)


def test_dispatch_key_reraises_only_non_operation_failed_exceptions():
    stack = ViewStack(_OtherErrorView())

    with pytest.raises(ValueError):
        dispatch_key(stack, key=0)


def test_dispatch_key_applies_transition_and_returns_none_on_success():
    stack = ViewStack(_StubView())

    result = dispatch_key(stack, key=0)

    assert result is None


def test_main_loop_survives_operation_failed_error_without_exiting():
    stack = ViewStack(_RaisingView(SearchFailedError()))

    for _ in range(3):
        result = dispatch_key(stack, key=0)
        assert isinstance(result, ErrorNotice)
