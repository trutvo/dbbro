import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.ui.fields import build_fields
from dbbro.ui.relation_rows import build_display_rows


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
def conn_with_shops():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE Shop (id TEXT, tsId TEXT, name TEXT, primeMembership_id TEXT)"
    )
    yield conn
    conn.close()


def test_build_display_rows_emits_a_row_per_match_with_no_cap(
    membership_shop_config, conn_with_shops
):
    for i in range(500):
        conn_with_shops.execute(
            "INSERT INTO Shop VALUES (?, ?, ?, ?)", (str(i), str(i), f"Shop{i}", "123456")
        )
    conn_with_shops.commit()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    continuation_rows = [r for r in rows if r[0] == ""]
    assert len(continuation_rows) == 500


def test_table_view_holds_all_rows_uncapped(membership_shop_config, conn_with_shops):
    from dbbro.navigation.breadcrumb import Breadcrumb
    from dbbro.ui.table_view import TableView

    for i in range(500):
        conn_with_shops.execute(
            "INSERT INTO Shop VALUES (?, ?, ?, ?)", (str(i), str(i), f"Shop{i}", "123456")
        )
    conn_with_shops.commit()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    view = TableView(
        table,
        record,
        conn_with_shops,
        membership_shop_config,
        Breadcrumb(),
        visible_height=5,
    )
    assert len(view.rows) == 502
