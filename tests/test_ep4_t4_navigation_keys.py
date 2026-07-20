from dbbro.history.history import History
from dbbro.ui import keys
from dbbro.ui.app import consumes_navigation_keys, handle_navigation_keys
from dbbro.ui.search_prompt import SearchValuePrompt
from dbbro.ui.view_stack import ViewStack


class _StubView:
    def consumes_navigation_keys(self) -> bool:
        return False

    def render(self, screen):
        pass

    def handle_key(self, key):
        return None


def test_left_right_navigate_history_when_current_view_does_not_consume_navigation_keys():
    history = History()
    view_a, view_b = _StubView(), _StubView()
    history.add_entry(view_a)
    history.add_entry(view_b)
    stack = ViewStack(view_b)

    assert not consumes_navigation_keys(stack.current)
    handle_navigation_keys(keys.LEFT, stack, history)

    assert stack.current is view_a


def test_left_right_move_cursor_when_search_prompt_view_consumes_navigation_keys():
    history = History()
    history.add_entry(_StubView())
    prompt = SearchValuePrompt("Employee", "name", history=history)
    prompt.buffer = "abc"
    prompt.cursor = 3

    assert consumes_navigation_keys(prompt) is True
    prompt.handle_key(keys.LEFT)

    assert prompt.cursor == 2
    assert prompt.buffer == "abc"
    assert history.current().view.__class__ is _StubView().__class__


def test_left_right_navigate_history_immediately_after_search_prompt_view_is_popped():
    history = History()
    view_a, view_b = _StubView(), _StubView()
    history.add_entry(view_a)
    history.add_entry(view_b)
    stack = ViewStack(view_b)
    prompt = SearchValuePrompt("Employee", "name", history=history)
    stack.push(prompt)
    assert consumes_navigation_keys(stack.current)

    stack.pop()  # simulate Escape popping the prompt

    assert not consumes_navigation_keys(stack.current)
    handle_navigation_keys(keys.LEFT, stack, history)
    assert stack.current is view_a
