from dbbro.config.models import Table
from dbbro.navigation.breadcrumb import Breadcrumb
from dbbro.ui import keys
from dbbro.ui.table_view import TableView

TABLE = Table(name="Company", columns=("a", "b", "c"), primary_key="a")
RECORD = {"a": "1", "b": "2", "c": "3"}


def _view(**kwargs):
    return TableView(TABLE, RECORD, conn=None, config=None, breadcrumb=Breadcrumb(), **kwargs)


def test_selection_moves_down_to_next_field():
    view = _view()

    view.handle_key(keys.DOWN)

    assert view.selected == 1


def test_selection_wraps_from_last_to_first_on_down():
    view = _view()
    view.selected = len(view.fields) - 1

    view.handle_key(keys.DOWN)

    assert view.selected == 0


def test_selection_wraps_from_first_to_last_on_up():
    view = _view()

    view.handle_key(keys.UP)

    assert view.selected == len(view.fields) - 1


def test_exactly_one_field_selected_at_a_time():
    view = _view()

    view.handle_key(keys.DOWN)
    view.handle_key(keys.DOWN)

    assert isinstance(view.selected, int)
    assert 0 <= view.selected < len(view.fields)


def test_scroll_offset_advances_when_selection_moves_past_visible_window():
    view = _view(visible_height=2)

    view.handle_key(keys.DOWN)
    view.handle_key(keys.DOWN)

    assert view.scroll_offset == 1


def test_scroll_offset_unchanged_when_selection_stays_within_visible_window():
    view = _view(visible_height=2)

    view.handle_key(keys.DOWN)

    assert view.scroll_offset == 0


def test_no_separate_scroll_keys_needed_up_down_alone_scrolls():
    view = _view(visible_height=2)

    view.handle_key(keys.DOWN)
    view.handle_key(keys.DOWN)

    assert view.scroll_offset == 1
    assert view.selected == 2
