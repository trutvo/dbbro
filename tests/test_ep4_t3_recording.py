import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.history.history import History
from dbbro.navigation.breadcrumb import Breadcrumb
from dbbro.ui.errors import SearchFailedError
from dbbro.ui.search_dialog import SearchSelectionDialog
from dbbro.ui.table_view import TableView


@pytest.fixture
def rel_config():
    company = Table(name="Company", columns=("id", "name"), primary_key="id")
    employee = Table(
        name="Employee",
        columns=("id", "name", "company_id"),
        primary_key="id",
        search_columns=("name",),
        relations=(
            Relation(
                target_table="Company",
                local_column="company_id",
                foreign_column="id",
            ),
        ),
    )
    return Config(
        tables=MappingProxyType({"Company": company, "Employee": employee})
    )


@pytest.fixture
def rel_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Company (id TEXT, name TEXT)")
    conn.execute("CREATE TABLE Employee (id TEXT, name TEXT, company_id TEXT)")
    yield conn
    conn.close()


def test_add_entry_called_on_search_result_display(rel_conn, rel_config):
    rel_conn.execute("INSERT INTO Employee VALUES ('1', 'Alice', '42')")
    history = History()
    dialog = SearchSelectionDialog(
        [("Employee", "name")], conn=rel_conn, config=rel_config, history=history
    )

    prompt_transition = dialog.handle_key(13)  # Return -> opens value prompt
    prompt = prompt_transition.view
    for ch in "Alice":
        prompt.handle_key(ord(ch))
    prompt.handle_key(13)  # Return -> submits

    assert history.current() is not None
    assert history.current().view.record["name"] == "Alice"


def test_add_entry_called_on_relation_follow_display(rel_conn, rel_config):
    rel_conn.execute("INSERT INTO Company VALUES ('42', 'Acme')")
    history = History()
    breadcrumb = Breadcrumb()
    record = {"id": "1", "name": "Alice", "company_id": "42"}
    view = TableView(
        rel_config.tables["Employee"], record, rel_conn, rel_config, breadcrumb, history
    )
    history.add_entry(view)
    view.selected = 2  # company_id, the relation field

    view.handle_key(13)  # Return -> follows relation

    assert history.current().view.table.name == "Company"


def test_opening_search_dialog_alone_does_not_call_add_entry(rel_conn, rel_config):
    history = History()
    SearchSelectionDialog(
        [("Employee", "name")], conn=rel_conn, config=rel_config, history=history
    )

    assert history.current() is None


def test_submitting_search_value_without_a_resulting_view_does_not_call_add_entry(
    rel_conn, rel_config
):
    history = History()
    dialog = SearchSelectionDialog(
        [("Employee", "name")], conn=rel_conn, config=rel_config, history=history
    )
    prompt = dialog.handle_key(13).view
    for ch in "Nope":
        prompt.handle_key(ord(ch))

    with pytest.raises(SearchFailedError):
        prompt.handle_key(13)

    assert history.current() is None


def test_go_back_does_not_trigger_any_lookup_or_query(rel_conn, rel_config):
    history = History()
    breadcrumb = Breadcrumb()
    record_a = {"id": "1", "name": "Alice", "company_id": "42"}
    record_b = {"id": "2", "name": "Bob", "company_id": "42"}
    view_a = TableView(
        rel_config.tables["Employee"], record_a, rel_conn, rel_config, breadcrumb, history
    )
    history.add_entry(view_a)
    view_b = TableView(
        rel_config.tables["Employee"], record_b, rel_conn, rel_config, breadcrumb, history
    )
    history.add_entry(view_b)

    rel_conn.close()  # any attempted query would now raise

    entry = history.go_back()

    assert entry.view is view_a
