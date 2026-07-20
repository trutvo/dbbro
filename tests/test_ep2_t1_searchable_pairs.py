from dbbro.ui.app import build_view_stack
from dbbro.ui.search_dialog import SearchSelectionDialog


def test_search_selection_dialog_lists_all_searchable_pairs(two_table_config):
    dialog = SearchSelectionDialog(two_table_config.searchable_pairs())

    assert dialog.pairs == [("Company", "name")]


def test_search_selection_dialog_entry_shows_table_and_column(two_table_config):
    dialog = SearchSelectionDialog(two_table_config.searchable_pairs())

    table, column = dialog.pairs[0]

    assert table == "Company"
    assert column == "name"


def test_table_with_no_search_columns_contributes_no_entries(two_table_config):
    dialog = SearchSelectionDialog(two_table_config.searchable_pairs())

    assert all(table != "Employee" for table, _ in dialog.pairs)


def test_run_ui_pushes_search_selection_dialog_before_any_other_view(
    two_table_config,
):
    stack = build_view_stack(two_table_config)

    assert isinstance(stack.current, SearchSelectionDialog)
    assert len(stack.frames) == 1
