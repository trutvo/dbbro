import curses

from dbbro.ui.modals import ErrorNotice
from tests.stub_screen import StubScreen


def test_error_notice_handle_key_return_dismisses():
    notice = ErrorNotice("Search failed: no matching record was found.")

    assert notice.handle_key(curses.KEY_ENTER) is True


def test_error_notice_handle_key_other_keys_ignored():
    notice = ErrorNotice("Search failed: no matching record was found.")

    for key in (27, curses.KEY_UP, curses.KEY_DOWN, ord("s"), ord("a")):
        assert notice.handle_key(key) is False


def test_error_notice_render_does_not_raise():
    notice = ErrorNotice("Search failed: no matching record was found.")

    notice.render(screen=StubScreen())
