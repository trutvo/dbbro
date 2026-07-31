import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.ui.fields import build_fields
from dbbro.ui.relation_rows import DisplayRow, build_display_rows


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


def test_plain_column_produces_one_row_unchanged(membership_shop_config, conn_with_shops):
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    creation_rows = [r for r in rows if r.name.strip() == "creationDate"]
    assert creation_rows == [DisplayRow("    creationDate", "2025-11-05 00:39:34", "field")]


def test_relation_column_with_no_matches_produces_no_referenced_by_section(
    membership_shop_config, conn_with_shops
):
    # No Shop rows are inserted, so the "id" relation column has zero
    # matches: per the "sections/groups with zero rows are omitted
    # entirely" rule, no REFERENCED BY section (and no row for "id" at
    # all) should appear - only the FIELDS section with creationDate.
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    assert not any(r.value == "referenced by" for r in rows)
    assert not any(r.name.strip() == "id" for r in rows)
    assert rows[0] == DisplayRow("", "  Membership", "section")
    assert rows[1] == DisplayRow("    creationDate", "2025-11-05 00:39:34", "field")


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
    # Related rows are the "related"-kind rows inside the REFERENCED BY
    # section, one per matched Shop, showing every column of Shop as
    # "column=value" pairs (format_record), not just its search columns.
    related_rows = [r for r in rows if r.kind == "related"]
    assert related_rows == [
        DisplayRow("", "      id=1, tsId=1001, name=ShopA, primeMembership_id=123456", "related"),
        DisplayRow("", "      id=2, tsId=1002, name=ShopB, primeMembership_id=123456", "related"),
        DisplayRow("", "      id=3, tsId=1003, name=ShopC, primeMembership_id=123456", "related"),
    ]
    group_rows = [r for r in rows if r.kind == "group"]
    assert group_rows == [DisplayRow("", "    Shop.primeMembership_id (3)", "group")]


def test_continuation_rows_use_empty_column_name(membership_shop_config, conn_with_shops):
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("1", "1001", "ShopA", "123456")
    )
    conn_with_shops.commit()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    related_rows = [r for r in rows if r.kind == "related"]
    assert related_rows == [
        DisplayRow("", "      id=1, tsId=1001, name=ShopA, primeMembership_id=123456", "related")
    ]
    group_rows = [r for r in rows if r.kind == "group"]
    assert group_rows == [DisplayRow("", "    Shop.primeMembership_id (1)", "group")]


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
    creation_index = next(i for i, r in enumerate(rows) if r.name.strip() == "creationDate")
    assert rows[creation_index] == DisplayRow(
        "    creationDate", "2025-11-05 00:39:34", "field"
    )
    assert row_targets[creation_index] is None
