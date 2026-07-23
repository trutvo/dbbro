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
def conn_with_two_shops():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE Shop (id TEXT, tsId TEXT, name TEXT, primeMembership_id TEXT)"
    )
    conn.execute("INSERT INTO Shop VALUES ('1', '1001', 'ShopA', '123456')")
    conn.execute("INSERT INTO Shop VALUES ('2', '1002', 'ShopB', '123456')")
    conn.commit()
    yield conn
    conn.close()


class _FakeHistory:
    def __init__(self):
        self.entries = []

    def add_entry(self, view):
        self.entries.append(view)


def test_opening_related_entity_row_extends_breadcrumb_like_existing_flow(
    membership_shop_config, conn_with_two_shops
):
    breadcrumb = Breadcrumb()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    view = TableView(table, record, conn_with_two_shops, membership_shop_config, breadcrumb)
    view.selected = 2  # second Shop continuation row

    view.handle_key(keys.RETURN)

    stops = breadcrumb.as_list()
    assert stops[-1].table == "Shop"
    assert stops[-1].primary_key_value == "2"


def test_opening_related_entity_row_records_history_entry_like_existing_flow(
    membership_shop_config, conn_with_two_shops
):
    history = _FakeHistory()
    table = membership_shop_config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    view = TableView(
        table, record, conn_with_two_shops, membership_shop_config, Breadcrumb(), history=history
    )
    view.selected = 1  # first Shop continuation row

    transition = view.handle_key(keys.RETURN)

    assert history.entries == [transition.view]
