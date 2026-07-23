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
def empty_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE Shop (id TEXT, tsId TEXT, name TEXT, primeMembership_id TEXT)"
    )
    yield conn
    conn.close()


def test_enter_on_local_column_with_zero_matches_returns_none_not_raises(
    membership_shop_config, empty_conn
):
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    view = TableView(table, record, empty_conn, membership_shop_config, Breadcrumb())
    view.selected = 0  # local column ("id") row, 0 matches

    transition = view.handle_key(keys.RETURN)

    assert transition is None
