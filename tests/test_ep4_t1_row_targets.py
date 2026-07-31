import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.ui.fields import build_fields
from dbbro.ui.relation_rows import (
    DisplayRow,
    LocalColumnTarget,
    RelatedEntityTarget,
    build_display_rows,
)


# --- Inbound (Referenced By) fixtures: the target table's records point at
# this record via its primary key, producing group headers + RelatedEntityTarget
# related rows. ---


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


def test_plain_field_row_has_no_target(membership_shop_config, conn_with_shops):
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    creation_index = rows.index(DisplayRow("    creationDate", "2025-11-05 00:39:34", "field"))
    assert row_targets[creation_index] is None


def test_related_entity_row_target_holds_its_own_record(membership_shop_config, conn_with_shops):
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("1", "1001", "ShopA", "123456")
    )
    conn_with_shops.commit()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    related_index = rows.index(
        DisplayRow("", "      id=1, tsId=1001, name=ShopA, primeMembership_id=123456", "related")
    )
    target = row_targets[related_index]
    assert isinstance(target, RelatedEntityTarget)
    assert target.target_table == "Shop"
    assert target.record == {
        "id": "1",
        "tsId": "1001",
        "name": "ShopA",
        "primeMembership_id": "123456",
    }


# --- Outbound (References) fixtures: this record holds the FK column
# (not its primary key) pointing at the target table, producing a
# "reference" row with a LocalColumnTarget. ---


@pytest.fixture
def order_category_config():
    order = Table(
        name="Order",
        columns=("id", "categoryRef", "note"),
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


@pytest.fixture
def conn_with_categories():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Category (id TEXT, code TEXT, name TEXT)")
    yield conn
    conn.close()


def test_local_column_row_target_holds_first_relations_matches(
    order_category_config, conn_with_categories
):
    conn_with_categories.execute(
        "INSERT INTO Category VALUES (?, ?, ?)", ("1", "XYZ", "CategoryA")
    )
    conn_with_categories.execute(
        "INSERT INTO Category VALUES (?, ?, ?)", ("2", "XYZ", "CategoryB")
    )
    conn_with_categories.commit()
    table = order_category_config.tables["Order"]
    record = {"id": "99", "categoryRef": "XYZ", "note": "n/a"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, order_category_config, conn_with_categories)
    reference_index = rows.index(DisplayRow("    categoryRef", "Category[XYZ]", "reference"))
    target = row_targets[reference_index]
    assert isinstance(target, LocalColumnTarget)
    assert target.target_table == "Category"
    assert len(target.matches) == 2


def test_zero_match_relation_produces_local_column_target_with_empty_matches(
    order_category_config, conn_with_categories
):
    table = order_category_config.tables["Order"]
    record = {"id": "99", "categoryRef": "XYZ", "note": "n/a"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, order_category_config, conn_with_categories)
    reference_index = rows.index(DisplayRow("    categoryRef", "Category[XYZ]", "reference"))
    target = row_targets[reference_index]
    assert isinstance(target, LocalColumnTarget)
    assert target.matches == ()


@pytest.fixture
def multi_relation_order_config():
    order = Table(
        name="Order",
        columns=("id", "categoryRef", "note"),
        primary_key="id",
        search_columns=(),
        relations=(
            Relation(
                target_table="Category",
                local_column="categoryRef",
                foreign_column="code",
            ),
            Relation(
                target_table="Category2",
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
    category2 = Table(
        name="Category2",
        columns=("id", "code", "name"),
        primary_key="id",
        search_columns=("name",),
    )
    return Config(
        tables=MappingProxyType(
            {"Order": order, "Category": category, "Category2": category2}
        )
    )


@pytest.fixture
def conn_with_two_category_tables():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Category (id TEXT, code TEXT, name TEXT)")
    conn.execute("CREATE TABLE Category2 (id TEXT, code TEXT, name TEXT)")
    yield conn
    conn.close()


def test_multi_relation_local_column_target_reflects_first_configured_relation_only(
    multi_relation_order_config, conn_with_two_category_tables
):
    conn = conn_with_two_category_tables
    conn.execute("INSERT INTO Category VALUES ('1', 'XYZ', 'CategoryA')")
    conn.execute("INSERT INTO Category2 VALUES ('1', 'XYZ', 'Category2A')")
    conn.commit()
    table = multi_relation_order_config.tables["Order"]
    record = {"id": "99", "categoryRef": "XYZ", "note": "n/a"}
    fields = build_fields(table, record)
    rows, row_targets = build_display_rows(fields, table, multi_relation_order_config, conn)
    # fields.py's relations_by_local_column dict keeps the *last* relation
    # for a given local column, so the displayed value reflects Category2;
    # but build_display_rows itself walks table.relations in order and
    # uses column_relations[0] (Category, the first configured) for the
    # LocalColumnTarget - this is the "dict limitation" the test name
    # refers to.
    reference_index = rows.index(DisplayRow("    categoryRef", "Category2[XYZ]", "reference"))
    target = row_targets[reference_index]
    assert isinstance(target, LocalColumnTarget)
    assert target.target_table == "Category"
    assert len(target.matches) == 1
