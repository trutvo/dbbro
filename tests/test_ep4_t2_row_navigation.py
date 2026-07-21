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


def _view(config, conn, **kwargs):
    table = config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    return TableView(table, record, conn, config, Breadcrumb(), **kwargs)


def test_down_moves_through_every_row_including_continuation_rows(
    membership_shop_config, conn_with_three_shops
):
    view = _view(membership_shop_config, conn_with_three_shops)
    assert len(view.rows) == 5  # id, 3 shops, creationDate

    seen = [view.selected]
    for _ in range(4):
        view.handle_key(keys.DOWN)
        seen.append(view.selected)

    assert seen == [0, 1, 2, 3, 4]


def test_up_down_wraps_across_full_row_count(membership_shop_config, conn_with_three_shops):
    view = _view(membership_shop_config, conn_with_three_shops)

    view.handle_key(keys.UP)

    assert view.selected == len(view.rows) - 1

    for _ in range(len(view.rows) - 1):
        view.handle_key(keys.UP)
    assert view.selected == 0


def test_scroll_offset_tracks_selected_row_directly(membership_shop_config, conn_with_three_shops):
    view = _view(membership_shop_config, conn_with_three_shops, visible_height=2)

    for _ in range(3):
        view.handle_key(keys.DOWN)

    assert view.selected == 3
    assert view.scroll_offset == 2
