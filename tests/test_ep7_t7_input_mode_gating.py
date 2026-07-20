from dbbro.ui import keys
from dbbro.ui.app import consumes_navigation_keys
from dbbro.ui.search_prompt import SearchValuePrompt
from dbbro.ui.view_stack import ViewStack


def test_typing_s_while_search_prompt_focused_appends_to_buffer_not_navigation():
    prompt = SearchValuePrompt("Company", "name")

    prompt.handle_key(keys.S)

    assert prompt.buffer == "s"


def test_left_right_move_cursor_not_navigation_while_search_prompt_focused():
    prompt = SearchValuePrompt("Company", "name")
    prompt.buffer = "abc"
    prompt.cursor = 3

    prompt.handle_key(keys.LEFT)

    assert prompt.cursor == 2
    assert prompt.buffer == "abc"


def test_s_left_right_reactivate_globally_once_search_prompt_is_no_longer_current():
    class _StubView:
        def render(self, screen):
            pass

        def handle_key(self, key):
            return None

    prompt = SearchValuePrompt("Company", "name")
    stack = ViewStack(_StubView())
    stack.push(prompt)
    assert consumes_navigation_keys(stack.current) is True

    stack.pop()  # simulate Escape cancelling the prompt

    assert consumes_navigation_keys(stack.current) is False
