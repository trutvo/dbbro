import sqlite3
from types import MappingProxyType

from dbbro.config.models import Config, Relation, Table
from dbbro.ui.modals import ErrorNotice, QuitConfirmation
from dbbro.ui.search_dialog import SearchSelectionDialog
from dbbro.ui.search_prompt import SearchValuePrompt
from dbbro.ui.selection_list import SelectionList
from dbbro.ui.table_view import TableView


def _labels(help_keys):
    return {(k.key_label, k.action_label) for k in help_keys}


def _plain_table():
    return Table(name="Company", columns=("id", "name"), primary_key="id")


def test_table_view_omits_open_when_field_not_relation():
    table = _plain_table()
    view = TableView(table, {"id": 1, "name": "Acme"}, conn=None, config=None, breadcrumb=None)

    labels = _labels(view.help_keys())

    assert not any(action == "open" for _, action in labels)
    assert ("↑/↓", "move") in labels


def test_table_view_includes_open_when_relation_field_selected():
    table = Table(
        name="Company",
        columns=("id", "shop_id"),
        primary_key="id",
        relations=(Relation(target_table="Shop", local_column="shop_id", foreign_column="id", label="Shop"),),
    )
    shop = Table(name="Shop", columns=("id",), primary_key="id")
    config = Config(tables=MappingProxyType({"Company": table, "Shop": shop}))
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Shop (id TEXT)")
    conn.execute("INSERT INTO Shop VALUES ('5')")
    conn.commit()
    view = TableView(table, {"id": 1, "shop_id": 5}, conn=conn, config=config, breadcrumb=None)
    view.selected = 1  # the shop_id / RelationField

    labels = _labels(view.help_keys())

    assert ("enter", "open") in labels


def test_selection_list_help_keys_contents():
    view = SelectionList([{"id": 1}], on_select=lambda record: None)

    labels = _labels(view.help_keys())

    assert ("↑/↓", "move") in labels
    assert ("enter", "select") in labels
    assert ("esc", "back") in labels


def test_search_dialog_help_keys_contents():
    view = SearchSelectionDialog([("Company", "name")])

    labels = _labels(view.help_keys())

    assert ("↑/↓", "move") in labels
    assert ("enter", "search") in labels
    assert ("esc", "back") in labels


def test_search_prompt_help_keys_contents():
    view = SearchValuePrompt("Company", "name")

    labels = _labels(view.help_keys())

    assert ("enter", "search") in labels
    assert ("esc", "back") in labels


def test_error_notice_and_quit_confirmation_help_keys():
    error_labels = _labels(ErrorNotice("boom").help_keys())
    quit_labels = _labels(QuitConfirmation().help_keys())

    assert ("enter", "dismiss") in error_labels
    assert ("enter", "quit") in quit_labels
    assert ("esc", "cancel") in quit_labels
