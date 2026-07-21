from dbbro.history.history import History
from dbbro.ui.app import get_help_keys, global_help_keys, render_frame
from dbbro.ui.help_bar import HelpKey
from dbbro.ui.modals import ErrorNotice, QuitConfirmation
from dbbro.ui.view_stack import ViewStack
from tests.stub_screen import StubScreen


class _FakeView:
    def render(self, screen) -> None:
        pass

    def help_keys(self):
        return [HelpKey("↑/↓", "move", priority=0)]


class _NoHelpView:
    def render(self, screen) -> None:
        pass


def _last_row_text(screen, height=24):
    calls = [c for c in screen.calls if isinstance(c, tuple) and c[0] == height - 1]
    return "".join(c[2] for c in calls)


def test_get_help_keys_defaults_to_empty_list_when_undefined():
    assert get_help_keys(_NoHelpView()) == []


def test_get_help_keys_returns_view_help_keys():
    assert get_help_keys(_FakeView()) == [HelpKey("↑/↓", "move", priority=0)]


def test_global_help_keys_includes_quit_and_search_by_default():
    history = History()
    keys = global_help_keys(_NoHelpView(), history)
    actions = {(k.key_label, k.action_label) for k in keys}
    assert ("q", "quit") in actions
    assert ("s", "search") in actions


def test_global_help_keys_omits_back_forward_without_history():
    history = History()
    keys = global_help_keys(_NoHelpView(), history)
    actions = {a for _, a in ((k.key_label, k.action_label) for k in keys)}
    assert "back" not in actions
    assert "forward" not in actions


def test_global_help_keys_includes_back_when_history_allows():
    history = History()
    history.add_entry(object())
    history.add_entry(object())
    keys = global_help_keys(_NoHelpView(), history)
    actions = {(k.key_label, k.action_label) for k in keys}
    assert ("←", "back") in actions


def test_global_help_keys_omits_quit_search_when_view_consumes_navigation_keys():
    class _ConsumingView:
        def consumes_navigation_keys(self):
            return True

    history = History()
    keys = global_help_keys(_ConsumingView(), history)
    assert keys == []


def test_help_bar_present_on_initial_render():
    screen = StubScreen()
    stack = ViewStack(_FakeView())
    history = History()

    render_frame(screen, stack, None, history=history)

    text = _last_row_text(screen)
    assert "move" in text
    assert "quit" in text


def test_help_bar_updates_after_navigating_to_different_view():
    screen = StubScreen()
    stack = ViewStack(_FakeView())
    history = History()

    render_frame(screen, stack, None, history=history)
    text_before = _last_row_text(screen)

    screen2 = StubScreen()
    stack2 = ViewStack(_NoHelpView())
    render_frame(screen2, stack2, None, history=history)
    text_after = _last_row_text(screen2)

    assert text_before != text_after


def test_help_bar_visible_during_pending_error_modal():
    screen = StubScreen()
    stack = ViewStack(_NoHelpView())
    history = History()

    render_frame(screen, stack, ErrorNotice("boom"), history=history)

    text = _last_row_text(screen)
    assert "dismiss" in text


def test_help_bar_visible_during_quit_confirmation():
    screen = StubScreen()
    stack = ViewStack(_NoHelpView())
    history = History()

    render_frame(screen, stack, QuitConfirmation(), history=history)

    text = _last_row_text(screen)
    assert "quit" in text


def test_no_key_or_state_hides_help_bar():
    history = History()
    for pending_modal in (None, ErrorNotice("x"), QuitConfirmation()):
        screen = StubScreen()
        stack = ViewStack(_NoHelpView())
        render_frame(screen, stack, pending_modal, history=history)
        assert _last_row_text(screen) != ""
