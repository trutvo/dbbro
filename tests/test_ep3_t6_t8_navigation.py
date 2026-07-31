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


# Employee's rows, given nav_config: company_id is an outbound reference
# (its local_column "company_id" != Employee's primary key "id"), so the
# layout is [section FIELDS(0), field id(1), field name(2),
# section REFERENCES(3), reference company_id(4)].
COMPANY_ID_ROW_INDEX = 4


def test_return_on_relation_field_with_one_match_displays_new_table_view_with_first_field_selected(
    nav_conn, nav_config
):
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme')")
    view = _employee_view(nav_conn, nav_config)
    view.selected = COMPANY_ID_ROW_INDEX  # company_id, the relation field

    transition = view.handle_key(keys.RETURN)

    new_view = transition.view
    assert isinstance(new_view, TableView)
    assert new_view.table.name == "Company"
    assert new_view.record == {"id": "42", "name": "Acme"}
    # Company has no relations of its own, so its rows are just
    # [section FIELDS, field id, field name]; the first selectable row
    # (index 1, "id") is selected, not index 0 (the section header).
    assert new_view.selected == 1


def test_return_on_relation_field_with_one_match_extends_breadcrumb(nav_conn, nav_config):
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme')")
    breadcrumb = Breadcrumb()
    view = _employee_view(nav_conn, nav_config, breadcrumb=breadcrumb)
    view.selected = COMPANY_ID_ROW_INDEX

    view.handle_key(keys.RETURN)

    stops = breadcrumb.as_list()
    assert stops[-1].table == "Company"
    assert stops[-1].primary_key_value == "42"


def test_return_on_relation_field_with_zero_matches_does_nothing(
    nav_conn, nav_config
):
    view = _employee_view(nav_conn, nav_config)
    view.selected = COMPANY_ID_ROW_INDEX

    assert view.handle_key(keys.RETURN) is None


def test_return_on_non_relation_field_does_nothing(nav_conn, nav_config):
    view = _employee_view(nav_conn, nav_config)
    view.selected = 2  # name, not a relation

    transition = view.handle_key(keys.RETURN)

    assert transition is None


def test_enter_on_local_column_with_multiple_matches_does_not_open_selection_list(
    nav_conn, nav_config
):
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme One')")
    nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme Two')")
    view = _employee_view(nav_conn, nav_config)
    view.selected = COMPANY_ID_ROW_INDEX  # company_id, the local column row

    assert view.handle_key(keys.RETURN) is None


# --- Inbound relation fixtures, for testing that a specific "related"
# row (kind="related", under a Referenced By group) opens its own record
# directly even when its group has multiple entries - unlike an outbound
# Reference row with multiple ambiguous matches, which refuses to open. ---


@pytest.fixture
def inbound_nav_config():
    company = Table(name="Company", columns=("id", "name", "employee_id"), primary_key="id")
    employee = Table(
        name="Employee",
        columns=("id", "name"),
        primary_key="id",
        relations=(
            Relation(
                target_table="Company",
                local_column="id",
                foreign_column="employee_id",
            ),
        ),
    )
    return Config(tables=MappingProxyType({"Company": company, "Employee": employee}))


@pytest.fixture
def inbound_nav_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Company (id TEXT, name TEXT, employee_id TEXT)")
    yield conn
    conn.close()


def test_enter_on_a_specific_related_entity_row_opens_it_directly(
    inbound_nav_conn, inbound_nav_config
):
    inbound_nav_conn.execute("INSERT INTO Company VALUES ('42', 'Acme One', '1')")
    inbound_nav_conn.execute("INSERT INTO Company VALUES ('43', 'Acme Two', '1')")
    record = {"id": "1", "name": "Alice"}
    view = TableView(
        inbound_nav_config.tables["Employee"],
        record,
        inbound_nav_conn,
        inbound_nav_config,
        Breadcrumb(),
    )
    # "id" is Employee's own primary key and its own relation's
    # local_column, so it becomes purely a Referenced By group (no plain
    # field row for it). rows = [section FIELDS(0), field name(1),
    # section REFERENCED BY(2), group header(3), related "Acme One"(4),
    # related "Acme Two"(5)].
    view.selected = 4  # the first related-entity row beneath the group header

    transition = view.handle_key(keys.RETURN)

    new_view = transition.view
    assert isinstance(new_view, TableView)
    assert new_view.table.name == "Company"
    assert new_view.record == {"id": "42", "name": "Acme One", "employee_id": "1"}
    assert new_view.selected == 1
