from dbbro.ui import keys
from dbbro.ui.modals import ErrorNotice
from dbbro.ui.search_dialog import SearchSelectionDialog
from dbbro.ui.search_prompt import SearchValuePrompt
from dbbro.ui.selection_list import SelectionList
from dbbro.ui.table_view import TableView
from dbbro.config.models import Table
from dbbro.navigation.breadcrumb import Breadcrumb
from tests.stub_screen import StubScreen


def test_search_selection_dialog_render_calls_draw_modal_with_all_pairs_and_highlighted_index():
    import curses

    dialog = SearchSelectionDialog([("Company", "name"), ("Company", "uuid")])
    screen = StubScreen()

    dialog.render(screen)

    text = screen.all_text()
    assert "Company.name" in text
    assert "Company.uuid" in text
    reverse_calls = [c for c in screen.calls if isinstance(c, tuple) and c[3] & curses.A_REVERSE]
    assert len(reverse_calls) == 1
    assert "Company.name" in reverse_calls[0][2]


def test_search_selection_dialog_scroll_offset_updates_on_down_up():
    pairs = [("T", str(i)) for i in range(30)]
    dialog = SearchSelectionDialog(pairs, visible_height=5)

    for _ in range(10):
        dialog.handle_key(keys.DOWN)

    assert dialog.highlighted == 10
    assert dialog.scroll_offset == 6


def test_search_value_prompt_render_calls_draw_modal_with_label_and_buffer():
    prompt = SearchValuePrompt("Company", "name")
    prompt.buffer = "Acme"
    screen = StubScreen()

    prompt.render(screen)

    text = screen.all_text()
    assert "Company.name" in text
    assert "Acme" in text


def test_table_view_render_calls_draw_panel_with_fields_and_selected_index():
    table = Table(name="Company", columns=("id", "name"), primary_key="id")
    record = {"id": "1", "name": "Acme"}
    view = TableView(table, record, conn=None, config=None, breadcrumb=Breadcrumb())
    screen = StubScreen()

    view.render(screen)

    text = screen.all_text()
    assert "Company" in text
    assert "id" in text
    assert "Acme" in text


def test_selection_list_render_calls_draw_modal_with_records_and_highlighted_index():
    records = [{"id": "1"}, {"id": "2"}]
    selection = SelectionList(records, on_select=lambda r: r)
    screen = StubScreen()

    selection.render(screen)

    text = screen.all_text()
    assert "1" in text
    assert "2" in text


def test_selection_list_scroll_offset_updates_on_down_up():
    records = [{"id": str(i)} for i in range(30)]
    selection = SelectionList(records, on_select=lambda r: r, visible_height=5)

    for _ in range(10):
        selection.handle_key(keys.DOWN)

    assert selection.highlighted == 10
    assert selection.scroll_offset == 6


def test_error_notice_render_calls_draw_modal_with_message():
    notice = ErrorNotice("Search failed: no matching record was found.")
    screen = StubScreen()

    notice.render(screen)

    assert "Search failed" in screen.all_text()
