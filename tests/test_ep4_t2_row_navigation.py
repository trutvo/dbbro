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
    # rows = [section FIELDS, field id, field creationDate,
    # section REFERENCED BY, group header, related shop0, related shop1,
    # related shop2] - "id" is Membership's own primary key/relation
    # column, so besides its own field row it also drives the Referenced
    # By group below.
    assert len(view.rows) == 8

    selectable_indices = [i for i, r in enumerate(view.rows) if r.selectable]
    assert selectable_indices == [1, 2, 5, 6, 7]

    seen = [view.selected]
    for _ in range(5):
        view.handle_key(keys.DOWN)
        seen.append(view.selected)

    # Moving down visits every selectable row (both fields, then each
    # related-entity row), then wraps back to the first.
    assert seen == [1, 2, 5, 6, 7, 1]


def test_up_down_wraps_across_full_row_count(membership_shop_config, conn_with_three_shops):
    view = _view(membership_shop_config, conn_with_three_shops)
    selectable_indices = [i for i, r in enumerate(view.rows) if r.selectable]
    assert view.selected == selectable_indices[0]

    view.handle_key(keys.UP)

    assert view.selected == selectable_indices[-1]

    # A full cycle through the remaining selectable rows (moving up)
    # returns to the starting selectable row.
    for _ in range(len(selectable_indices) - 1):
        view.handle_key(keys.UP)
    assert view.selected == selectable_indices[0]


def test_scroll_offset_tracks_selected_row_directly(membership_shop_config, conn_with_three_shops):
    view = _view(membership_shop_config, conn_with_three_shops, visible_height=2)

    for _ in range(3):
        view.handle_key(keys.DOWN)

    # selected walks 1 -> 2 -> 5 -> 6 (the selectable rows), and the
    # scroll window re-clamps around each in turn.
    assert view.selected == 6
    assert view.scroll_offset == 5
