import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.navigation.breadcrumb import Breadcrumb
from dbbro.ui import keys
from dbbro.ui.table_view import TableView


@pytest.fixture
def nav_config():
    company = Table(name="Company", columns=("id", "name"), primary_key="id")
    employee = Table(
        name="Employee",
        columns=("id", "name", "company_id"),
        primary_key="id",
        relations=(
            Relation(
                target_table="Company",
                local_column="company_id",
                foreign_column="id",
                label="belongs to company",
            ),
        ),
    )
    return Config(
        tables=MappingProxyType({"Company": company, "Employee": employee})
    )


@pytest.fixture
def nav_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Company (id TEXT, name TEXT)")
    conn.execute("CREATE TABLE Employee (id TEXT, name TEXT, company_id TEXT)")
    yield conn
    conn.close()


def _employee_view(nav_conn, nav_config, breadcrumb=None):
    record = {"id": "1", "name": "Alice", "company_id": "42"}
    return TableView(
        nav_config.tables["Employee"],
        record,
        nav_conn,
        nav_config,
        breadcrumb or Breadcrumb(),
    )


def test_return_on_relation_field_with_one_match_displays_new_table_view_with_first_field_selected(
    nav_conn, nav_config
):
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme')")
    view = _employee_view(nav_conn, nav_config)
    view.selected = 2  # company_id, the relation field

    transition = view.handle_key(keys.RETURN)

    new_view = transition.view
    assert isinstance(new_view, TableView)
    assert new_view.table.name == "Company"
    assert new_view.record == {"id": "42", "name": "Acme"}
    assert new_view.selected == 0


def test_return_on_relation_field_with_one_match_extends_breadcrumb(nav_conn, nav_config):
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme')")
    breadcrumb = Breadcrumb()
    view = _employee_view(nav_conn, nav_config, breadcrumb=breadcrumb)
    view.selected = 2

    view.handle_key(keys.RETURN)

    stops = breadcrumb.as_list()
    assert stops[-1].table == "Company"
    assert stops[-1].primary_key_value == "42"


def test_return_on_relation_field_with_zero_matches_does_nothing(
    nav_conn, nav_config
):
    view = _employee_view(nav_conn, nav_config)
    view.selected = 2

    assert view.handle_key(keys.RETURN) is None


def test_return_on_non_relation_field_does_nothing(nav_conn, nav_config):
    view = _employee_view(nav_conn, nav_config)
    view.selected = 1  # name, not a relation

    transition = view.handle_key(keys.RETURN)

    assert transition is None


def test_enter_on_local_column_with_multiple_matches_does_not_open_selection_list(
    nav_conn, nav_config
):
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme One')")
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme Two')")
    view = _employee_view(nav_conn, nav_config)
    view.selected = 2  # company_id, the local column row

    assert view.handle_key(keys.RETURN) is None


def test_enter_on_a_specific_related_entity_row_opens_it_directly(nav_conn, nav_config):
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme One')")
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme Two')")
    view = _employee_view(nav_conn, nav_config)
    view.selected = 3  # first related-entity row beneath company_id

    transition = view.handle_key(keys.RETURN)

    new_view = transition.view
    assert isinstance(new_view, TableView)
    assert new_view.table.name == "Company"
    assert new_view.record == {"id": "42", "name": "Acme One"}
    assert new_view.selected == 0
