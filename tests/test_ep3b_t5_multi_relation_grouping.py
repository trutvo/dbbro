import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.ui.fields import build_fields
from dbbro.ui.relation_rows import build_display_rows


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
            ),
            Relation(
                target_table="Orders",
                local_column="id",
                foreign_column="membership_id",
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


def test_two_relations_on_same_local_column_both_produce_rows(
    multi_relation_config, conn_with_shops_and_orders
):
    conn = conn_with_shops_and_orders
    conn.execute("INSERT INTO Shop VALUES ('1', '1001', 'ShopA', '123456')")
    conn.execute("INSERT INTO Orders VALUES ('1', 'ORD1', '123456')")
    conn.commit()
    table = multi_relation_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, multi_relation_config, conn)
    assert ("", "=> Shop[1001]") in rows
    assert ("", "=> Orders[ORD1]") in rows


def test_relation_groups_appear_in_table_relations_order(
    multi_relation_config, conn_with_shops_and_orders
):
    conn = conn_with_shops_and_orders
    conn.execute("INSERT INTO Shop VALUES ('1', '1001', 'ShopA', '123456')")
    conn.execute("INSERT INTO Orders VALUES ('1', 'ORD1', '123456')")
    conn.commit()
    table = multi_relation_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, multi_relation_config, conn)
    shop_index = rows.index(("", "=> Shop[1001]"))
    order_index = rows.index(("", "=> Orders[ORD1]"))
    assert shop_index < order_index


def test_relations_by_local_column_dict_limitation_does_not_drop_a_relation(
    multi_relation_config, conn_with_shops_and_orders
):
    conn = conn_with_shops_and_orders
    conn.execute("INSERT INTO Shop VALUES ('1', '1001', 'ShopA', '123456')")
    conn.execute("INSERT INTO Orders VALUES ('1', 'ORD1', '123456')")
    conn.commit()
    table = multi_relation_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, multi_relation_config, conn)
    continuation_rows = [r for r in rows if r[0] == ""]
    assert len(continuation_rows) == 2
