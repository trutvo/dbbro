from dbbro.config.models import Table
from dbbro.navigation.breadcrumb import Breadcrumb
from dbbro.ui import keys
from dbbro.ui.table_view import TableView

TABLE = Table(name="Company", columns=("a", "b", "c"), primary_key="a")
RECORD = {"a": "1", "b": "2", "c": "3"}


def _view(**kwargs):
    return TableView(TABLE, RECORD, conn=None, config=None, breadcrumb=Breadcrumb(), **kwargs)


def test_selection_moves_down_to_next_field():
    # rows = [section FIELDS, field a, field b, field c]; the section
    # header is not selectable, so selection starts on "a" (row 1) and
    # moving down lands on "b" (row 2).
    view = _view()
    assert view.selected == 1

    view.handle_key(keys.DOWN)

    assert view.selected == 2


def test_selection_wraps_from_last_to_first_on_down():
    view = _view()
    view.selected = len(view.rows) - 1  # last row: field "c"

    view.handle_key(keys.DOWN)

    assert view.selected == 1  # wraps to first selectable row: field "a"


def test_selection_wraps_from_first_to_last_on_up():
    view = _view()
    assert view.selected == 1  # first selectable row: field "a"

    view.handle_key(keys.UP)

    assert view.selected == len(view.rows) - 1  # wraps to last row: field "c"


def test_exactly_one_field_selected_at_a_time():
    view = _view()

    view.handle_key(keys.DOWN)
    view.handle_key(keys.DOWN)

    assert isinstance(view.selected, int)
    assert 0 <= view.selected < len(view.rows)
    assert view.rows[view.selected].selectable


def test_scroll_offset_advances_when_selection_moves_past_visible_window():
    # rows = [section, a, b, c]; visible_height=2 shows only 2 rows at a
    # time. Selection starts at row 1 ("a"); each DOWN moves to the next
    # selectable row and re-clamps the scroll window around it.
    view = _view(visible_height=2)

    view.handle_key(keys.DOWN)  # selected -> 2 ("b"), scroll_offset -> 1
    view.handle_key(keys.DOWN)  # selected -> 3 ("c"), scroll_offset -> 2

    assert view.selected == 3
    assert view.scroll_offset == 2


def test_scroll_offset_unchanged_when_selection_stays_within_visible_window():
    # A visible_height wide enough (3) to hold the section header row plus
    # the first two fields, so moving from "a" (row 1) to "b" (row 2)
    # stays inside the current window and the scroll offset doesn't move.
    view = _view(visible_height=3)

    view.handle_key(keys.DOWN)

    assert view.scroll_offset == 0


def test_no_separate_scroll_keys_needed_up_down_alone_scrolls():
    view = _view(visible_height=2)

    view.handle_key(keys.DOWN)
    view.handle_key(keys.DOWN)

    assert view.scroll_offset == 2
    assert view.selected == 3
