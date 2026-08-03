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


def test_zero_matches_produce_no_continuation_rows(membership_shop_config, conn_with_shops):
    # With zero matches, the relation contributes no REFERENCED BY section,
    # group header, or related rows - but the id column itself still shows
    # as a plain field, same as any other column.
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    assert rows == [
        DisplayRow("", "  Membership", "section"),
        DisplayRow("    id", "123456", "field"),
        DisplayRow("    creationDate", "2025-11-05 00:39:34", "field"),
    ]


def test_single_match_produces_exactly_one_continuation_row(membership_shop_config, conn_with_shops):
    conn_with_shops.execute(
        "INSERT INTO Shop VALUES (?, ?, ?, ?)", ("1", "1001", "ShopA", "123456")
    )
    conn_with_shops.commit()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    fields = build_fields(table, record)
    rows, _ = build_display_rows(fields, table, membership_shop_config, conn_with_shops)
    assert rows == [
        DisplayRow("", "  Membership", "section"),
        DisplayRow("    id", "123456", "field"),
        DisplayRow("    creationDate", "2025-11-05 00:39:34", "field"),
        DisplayRow("", "  referenced by", "section"),
        DisplayRow("", "    primeMembership_id (1)", "group"),
        DisplayRow("", "      Shop[1]", "related"),
    ]
