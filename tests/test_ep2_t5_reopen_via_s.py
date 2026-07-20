from dbbro.ui import keys
from dbbro.ui.search_dialog import SearchSelectionDialog
from dbbro.ui.search_prompt import SearchValuePrompt
from dbbro.ui.view_stack import ViewStack


class _StubView:
    def render(self, screen):
        pass

    def handle_key(self, key):
        return None


def test_s_key_opens_selection_dialog_when_on_an_arbitrary_view(two_table_config):
    stack = ViewStack(_StubView())

    stack.reset_to(SearchSelectionDialog(two_table_config.searchable_pairs()))

    assert isinstance(stack.current, SearchSelectionDialog)


def test_reopened_dialog_lists_same_pairs_highlight_on_first(two_table_config):
    stack = ViewStack(_StubView())
    stack.current.handle_key(keys.DOWN)

    stack.reset_to(SearchSelectionDialog(two_table_config.searchable_pairs()))

    assert stack.current.pairs == two_table_config.searchable_pairs()
    assert stack.current.highlighted == 0


def test_s_key_mid_entry_in_value_prompt_discards_buffer(two_table_config):
    prompt = SearchValuePrompt("Company", "name")
    prompt.handle_key(ord("A"))
    stack = ViewStack(_StubView())
    stack.push(prompt)

    stack.reset_to(SearchSelectionDialog(two_table_config.searchable_pairs()))

    assert isinstance(stack.current, SearchSelectionDialog)
    assert stack.frames == [stack.frames[0], stack.current]
