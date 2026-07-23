import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.navigation.breadcrumb import Breadcrumb
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


def _conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE Shop (id TEXT, tsId TEXT, name TEXT, primeMembership_id TEXT)"
    )
    return conn


def _seed(conn, count):
    for i in range(count):
        conn.execute(
            "INSERT INTO Shop VALUES (?, ?, ?, ?)", (str(i), str(i), f"Shop{i}", "123456")
        )
    conn.commit()


def _labels(help_keys):
    return {(k.key_label, k.action_label) for k in help_keys}


def _view(config, conn):
    table = config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    return TableView(table, record, conn, config, Breadcrumb())


def test_help_shows_enter_open_for_related_entity_row(membership_shop_config):
    conn = _conn()
    _seed(conn, 1)
    view = _view(membership_shop_config, conn)
    view.selected = 1  # the Shop continuation row

    assert ("enter", "open") in _labels(view.help_keys())


def test_help_shows_enter_open_for_single_match_local_column_row(membership_shop_config):
    conn = _conn()
    _seed(conn, 1)
    view = _view(membership_shop_config, conn)
    view.selected = 0  # local column row, exactly one match

    assert ("enter", "open") in _labels(view.help_keys())


def test_help_omits_enter_open_for_multi_match_local_column_row(membership_shop_config):
    conn = _conn()
    _seed(conn, 3)
    view = _view(membership_shop_config, conn)
    view.selected = 0  # local column row, 3 matches

    assert ("enter", "open") not in _labels(view.help_keys())


def test_help_omits_enter_open_for_zero_match_local_column_row(membership_shop_config):
    conn = _conn()
    view = _view(membership_shop_config, conn)
    view.selected = 0  # local column row, 0 matches

    assert ("enter", "open") not in _labels(view.help_keys())


def test_help_omits_enter_open_for_plain_field_row(membership_shop_config):
    conn = _conn()
    _seed(conn, 1)
    view = _view(membership_shop_config, conn)
    view.selected = 2  # creationDate, not a relation

    assert ("enter", "open") not in _labels(view.help_keys())
