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
def conn_with_shops():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE Shop (id TEXT, tsId TEXT, name TEXT, primeMembership_id TEXT)"
    )
    yield conn
    conn.close()


def test_plain_column_produces_one_row_unchanged(membership_shop_config, conn_with_shops):
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    creation_rows = [r for r in rows if r[0] == "creationDate"]
    assert creation_rows == [("creationDate", "2025-11-05 00:39:34")]


def test_relation_column_first_row_shows_raw_local_value(membership_shop_config, conn_with_shops):
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    assert rows[0] == ("id", "123456")


def test_relation_column_appends_one_row_per_matched_related_entity(
    membership_shop_config, conn_with_shops
):
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("1", "1001", "ShopA", "123456")
    )
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("2", "1002", "ShopB", "123456")
    )
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("3", "1003", "ShopC", "123456")
    )
    conn_with_shops.commit()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    continuation_rows = [r for r in rows if r[0] == ""]
    assert continuation_rows == [
        ("", "=> Shop[1001]"),
        ("", "=> Shop[1002]"),
        ("", "=> Shop[1003]"),
    ]


def test_continuation_rows_use_empty_column_name(membership_shop_config, conn_with_shops):
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("1", "1001", "ShopA", "123456")
    )
    conn_with_shops.commit()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    assert rows[1] == ("", "=> Shop[1001]")


def test_row_targets_are_parallel_to_rows(membership_shop_config, conn_with_shops):
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("1", "1001", "ShopA", "123456")
    )
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("2", "1002", "ShopB", "123456")
    )
    conn_with_shops.commit()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    assert len(row_targets) == len(rows)
    assert rows[3] == ("creationDate", "2025-11-05 00:39:34")
    assert row_targets[3] is None
