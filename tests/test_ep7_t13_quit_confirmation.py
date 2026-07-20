import curses

from dbbro.ui import keys
from dbbro.ui.modals import QuitConfirmation
from dbbro.ui.search_prompt import SearchValuePrompt
from tests.stub_screen import StubScreen


def test_quit_confirmation_return_confirms():
    modal = QuitConfirmation()

    assert modal.handle_key(curses.KEY_ENTER) == "confirm"


def test_quit_confirmation_escape_cancels():
    modal = QuitConfirmation()

    assert modal.handle_key(keys.ESCAPE) == "cancel"


def test_quit_confirmation_other_keys_ignored():
    modal = QuitConfirmation()

    assert modal.handle_key(ord("y")) is None
    assert modal.handle_key(curses.KEY_UP) is None


def test_quit_confirmation_renders_a_message():
    modal = QuitConfirmation()
    screen = StubScreen()

    modal.render(screen)

    assert "Quit" in screen.all_text()


def test_typing_q_while_search_prompt_focused_appends_to_buffer_not_quit():
    prompt = SearchValuePrompt("Company", "name")

    prompt.handle_key(keys.Q)

    assert prompt.buffer == "q"
