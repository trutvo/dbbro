import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.navigation.breadcrumb import Breadcrumb
from dbbro.ui.table_view import TableView


@pytest.fixture
def order_category_config():
    # An *outbound* relation fixture (this record holds the FK column,
    # categoryRef, which is not its own primary key), so it always
    # produces a REFERENCES section with exactly one reference row for
    # categoryRef - regardless of how many Category rows match - unlike
    # the *inbound* membership_shop_config below, whose Referenced By
    # rows only appear when there's at least one match.
    order = Table(
        name="Order",
        columns=("id", "categoryRef"),
        primary_key="id",
        search_columns=(),
        relations=(
            Relation(
                target_table="Category",
                local_column="categoryRef",
                foreign_column="code",
            ),
        ),
    )
    category = Table(
        name="Category",
        columns=("id", "code", "name"),
        primary_key="id",
        search_columns=("name",),
    )
    return Config(tables=MappingProxyType({"Order": order, "Category": category}))


def _order_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Category (id TEXT, code TEXT, name TEXT)")
    return conn


def _seed_categories(conn, count):
    for i in range(count):
        conn.execute(
            "INSERT INTO Category VALUES (?, ?, ?)", (str(i), "XYZ", f"Category{i}")
        )
    conn.commit()


def _order_view(config, conn):
    table = config.tables["Order"]
    record = {"id": "99", "categoryRef": "XYZ"}
    return TableView(table, record, conn, config, Breadcrumb())


@pytest.fixture
def membership_shop_config():
    membership = Table(
        name="Membership",
        columns=("id", "creationDate"),
        primary_key="id",
        search_columns=(),
        relations=(
            Relation(
                target_table="Shop",
                local_column="id",
                foreign_column="primeMembership_id",
            ),
        ),
    )
    shop = Table(
        name="Shop",
        columns=("id", "tsId", "name", "primeMembership_id"),
        primary_key="id",
        search_columns=("tsId",),
    )
    return Config(tables=MappingProxyType({"Membership": membership, "Shop": shop}))


def _conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE Shop (id TEXT, tsId TEXT, name TEXT, primeMembership_id TEXT)"
    )
    return conn


def _seed(conn, count):
    for i in range(count):
        conn.execute(
            "INSERT INTO Shop VALUES (?, ?, ?, ?)", (str(i), str(i), f"Shop{i}", "123456")
        )
    conn.commit()


def _labels(help_keys):
    return {(k.key_label, k.action_label) for k in help_keys}


def _view(config, conn):
    table = config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    return TableView(table, record, conn, config, Breadcrumb())


def test_help_shows_enter_open_for_related_entity_row(membership_shop_config):
    conn = _conn()
    _seed(conn, 1)
    view = _view(membership_shop_config, conn)
    # rows = [section FIELDS(0), field id(1), field creationDate(2),
    # section REFERENCED BY(3), group header(4), related shop(5)].
    view.selected = 5  # the Shop related row

    assert ("enter", "open") in _labels(view.help_keys())


def test_help_shows_enter_open_for_single_match_local_column_row(order_category_config):
    conn = _order_conn()
    _seed_categories(conn, 1)
    view = _order_view(order_category_config, conn)
    # rows = [section FIELDS(0), field id(1), section REFERENCES(2),
    # reference categoryRef(3)].
    view.selected = 3  # reference row, exactly one match

    assert ("enter", "open") in _labels(view.help_keys())


def test_help_omits_enter_open_for_multi_match_local_column_row(order_category_config):
    conn = _order_conn()
    _seed_categories(conn, 3)
    view = _order_view(order_category_config, conn)
    view.selected = 3  # reference row, 3 matches

    assert ("enter", "open") not in _labels(view.help_keys())


def test_help_omits_enter_open_for_zero_match_local_column_row(order_category_config):
    conn = _order_conn()
    view = _order_view(order_category_config, conn)
    view.selected = 3  # reference row, 0 matches

    assert ("enter", "open") not in _labels(view.help_keys())


def test_help_omits_enter_open_for_plain_field_row(membership_shop_config):
    conn = _conn()
    _seed(conn, 1)
    view = _view(membership_shop_config, conn)
    view.selected = 2  # creationDate, not a relation

    assert ("enter", "open") not in _labels(view.help_keys())
