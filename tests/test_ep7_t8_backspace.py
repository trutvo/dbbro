import curses

from dbbro.ui import keys
from dbbro.ui.search_prompt import SearchValuePrompt


def test_backspace_removes_character_before_cursor():
    prompt = SearchValuePrompt("Company", "name")
    prompt.buffer = "abc"
    prompt.cursor = 3

    prompt.handle_key(curses.KEY_BACKSPACE)

    assert prompt.buffer == "ab"
    assert prompt.cursor == 2


def test_backspace_removes_character_at_cursor_not_end_of_buffer():
    prompt = SearchValuePrompt("Company", "name")
    prompt.buffer = "abc"
    prompt.cursor = 1

    prompt.handle_key(curses.KEY_BACKSPACE)

    assert prompt.buffer == "bc"
    assert prompt.cursor == 0


def test_backspace_is_a_no_op_at_start_of_buffer():
    prompt = SearchValuePrompt("Company", "name")
    prompt.buffer = "abc"
    prompt.cursor = 0

    prompt.handle_key(curses.KEY_BACKSPACE)

    assert prompt.buffer == "abc"
    assert prompt.cursor == 0


def test_del_127_and_ascii_bs_8_also_work_as_backspace():
    for code in (127, 8):
        prompt = SearchValuePrompt("Company", "name")
        prompt.buffer = "x"
        prompt.cursor = 1

        prompt.handle_key(code)

        assert prompt.buffer == "", f"code {code} did not delete"
