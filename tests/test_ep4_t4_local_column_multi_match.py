import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.navigation.breadcrumb import Breadcrumb
from dbbro.ui import keys
from dbbro.ui.table_view import TableView


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
                label="has Shop",
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


@pytest.fixture
def conn_with_three_shops():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE Shop (id TEXT, tsId TEXT, name TEXT, primeMembership_id TEXT)"
    )
    for i in range(3):
        conn.execute(
            "INSERT INTO Shop VALUES (?, ?, ?, ?)", (str(i), str(i), f"Shop{i}", "123456")
        )
    conn.commit()
    yield conn
    conn.close()


def _view(config, conn):
    table = config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    return TableView(table, record, conn, config, Breadcrumb())


def test_enter_on_local_column_with_multiple_matches_returns_none(
    membership_shop_config, conn_with_three_shops
):
    view = _view(membership_shop_config, conn_with_three_shops)
    view.selected = 0  # local column ("id") row, 3 matches

    transition = view.handle_key(keys.RETURN)

    assert transition is None


def test_enter_on_local_column_with_multiple_matches_does_not_change_view(
    membership_shop_config, conn_with_three_shops
):
    view = _view(membership_shop_config, conn_with_three_shops)
    view.selected = 0
    rows_before = list(view.rows)

    view.handle_key(keys.RETURN)

    assert view.selected == 0
    assert view.rows == rows_before
