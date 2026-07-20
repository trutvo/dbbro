from dbbro.ui import keys
from dbbro.ui.search_dialog import SearchSelectionDialog
from dbbro.ui.search_prompt import SearchValuePrompt
from dbbro.ui.view_stack import Transition, TransitionKind


def _dialog():
    return SearchSelectionDialog([("Company", "name"), ("Company", "id")])


def test_down_moves_highlight_to_next_pair():
    dialog = _dialog()

    dialog.handle_key(keys.DOWN)

    assert dialog.highlighted == 1


def test_up_moves_highlight_to_previous_pair():
    dialog = _dialog()
    dialog.handle_key(keys.DOWN)

    dialog.handle_key(keys.UP)

    assert dialog.highlighted == 0


def test_return_on_highlighted_pair_pushes_value_prompt_labeled_correctly():
    dialog = _dialog()
    dialog.handle_key(keys.DOWN)

    transition = dialog.handle_key(keys.RETURN)

    assert transition.kind is TransitionKind.PUSH
    assert isinstance(transition.view, SearchValuePrompt)
    assert transition.view.table == "Company"
    assert transition.view.column == "id"


def test_escape_pops_selection_dialog_without_pushing():
    dialog = _dialog()

    transition = dialog.handle_key(keys.ESCAPE)

    assert transition == Transition.pop()
