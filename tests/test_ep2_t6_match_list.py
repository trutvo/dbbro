from dbbro.ui import keys
from dbbro.ui.selection_list import SelectionList
from dbbro.ui.view_stack import Transition, TransitionKind

RECORDS = [
    {"id": "1", "name": "Acme"},
    {"id": "2", "name": "Acme"},
    {"id": "3", "name": "Acme"},
]


def test_match_list_row_shows_every_configured_column_and_value():
    view = SelectionList(RECORDS, on_select=lambda record: record)

    assert view.records[0] == {"id": "1", "name": "Acme"}


def test_down_up_move_highlight_scrolling_with_no_match_count_limit():
    view = SelectionList(RECORDS, on_select=lambda record: record)

    for _ in range(len(RECORDS) + 1):
        view.handle_key(keys.DOWN)

    assert view.highlighted == 1

    view.handle_key(keys.UP)
    assert view.highlighted == 0


def test_return_on_highlighted_match_pushes_that_records_table_view():
    view = SelectionList(RECORDS, on_select=lambda record: ("table-view-for", record))
    view.handle_key(keys.DOWN)

    transition = view.handle_key(keys.RETURN)

    assert transition.kind is TransitionKind.PUSH
    assert transition.view == ("table-view-for", RECORDS[1])


def test_escape_pops_match_list_to_pre_search_view():
    view = SelectionList(RECORDS, on_select=lambda record: record)

    transition = view.handle_key(keys.ESCAPE)

    assert transition == Transition.pop()
