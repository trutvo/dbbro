import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.ui.fields import build_fields
from dbbro.ui.relation_rows import (
    LocalColumnTarget,
    RelatedEntityTarget,
    build_display_rows,
)


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


def test_plain_field_row_has_no_target(membership_shop_config, conn_with_shops):
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    creation_index = rows.index(("creationDate", "2025-11-05 00:39:34"))
    assert row_targets[creation_index] is None


def test_local_column_row_target_holds_first_relations_matches(
    membership_shop_config, conn_with_shops
):
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
    target = row_targets[rows.index(("id", "123456"))]
    assert isinstance(target, LocalColumnTarget)
    assert target.target_table == "Shop"
    assert len(target.matches) == 2


def test_related_entity_row_target_holds_its_own_record(membership_shop_config, conn_with_shops):
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("1", "1001", "ShopA", "123456")
    )
    conn_with_shops.commit()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    continuation_index = rows.index(("", "has Shop 1001"))
    target = row_targets[continuation_index]
    assert isinstance(target, RelatedEntityTarget)
    assert target.target_table == "Shop"
    assert target.record == {
        "id": "1",
        "tsId": "1001",
        "name": "ShopA",
        "primeMembership_id": "123456",
    }


def test_zero_match_relation_produces_local_column_target_with_empty_matches(
    membership_shop_config, conn_with_shops
):
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    target = row_targets[rows.index(("id", "123456"))]
    assert isinstance(target, LocalColumnTarget)
    assert target.matches == ()


@pytest.fixture
def multi_relation_config():
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
            Relation(
                target_table="Orders",
                local_column="id",
                foreign_column="membership_id",
                label="has Orders",
            ),
        ),
    )
    shop = Table(
        name="Shop",
        columns=("id", "tsId", "name", "primeMembership_id"),
        primary_key="id",
        search_columns=("tsId",),
    )
    order = Table(
        name="Orders",
        columns=("id", "ref", "membership_id"),
        primary_key="id",
        search_columns=("ref",),
    )
    return Config(
        tables=MappingProxyType({"Membership": membership, "Shop": shop, "Orders": order})
    )


@pytest.fixture
def conn_with_shops_and_orders():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE Shop (id TEXT, tsId TEXT, name TEXT, primeMembership_id TEXT)"
    )
    conn.execute("CREATE TABLE Orders (id TEXT, ref TEXT, membership_id TEXT)")
    yield conn
    conn.close()


def test_multi_relation_local_column_target_reflects_first_configured_relation_only(
    multi_relation_config, conn_with_shops_and_orders
):
    conn = conn_with_shops_and_orders
    conn.execute("INSERT INTO Shop VALUES ('1', '1001', 'ShopA', '123456')")
    conn.execute("INSERT INTO Orders VALUES ('1', 'ORD1', '123456')")
    conn.execute("INSERT INTO Orders VALUES ('2', 'ORD2', '123456')")
    conn.commit()
    table = multi_relation_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, multi_relation_config, conn)
    target = row_targets[rows.index(("id", "123456"))]
    assert isinstance(target, LocalColumnTarget)
    assert target.target_table == "Shop"
    assert len(target.matches) == 1
