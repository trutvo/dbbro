import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Relation, Table
from dbbro.navigation.breadcrumb import Breadcrumb
from dbbro.ui import keys
from dbbro.ui.selection_list import SelectionList
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
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE Shop (id TEXT, tsId TEXT, name TEXT, primeMembership_id TEXT)"
    )
    yield conn
    conn.close()


def _view(config, conn, **kwargs):
    table = config.tables["Membership"]
    record = {"id": "123456", "creationDate": "2025-11-05 00:39:34"}
    return TableView(table, record, conn, config, Breadcrumb(), **kwargs)


def test_enter_on_related_entity_row_pushes_that_records_table_view(
    membership_shop_config, conn
):
    conn.execute("INSERT INTO Shop VALUES (?, ?, ?, ?)", ("1", "1001", "ShopA", "123456"))
    conn.execute("INSERT INTO Shop VALUES (?, ?, ?, ?)", ("2", "1002", "ShopB", "123456"))
    conn.commit()
    view = _view(membership_shop_config, conn)
    # rows = [section FIELDS(0), field creationDate(1),
    # section REFERENCED BY(2), group header(3), related shop1(4),
    # related shop2(5)].
    view.selected = 5  # second Shop related row

    transition = view.handle_key(keys.RETURN)

    assert isinstance(transition.view, TableView)
    assert transition.view.table.name == "Shop"
    assert transition.view.record == {
        "id": "2",
        "tsId": "1002",
        "name": "ShopB",
        "primeMembership_id": "123456",
    }


def test_enter_on_related_entity_row_never_shows_a_selection_list(
    membership_shop_config, conn
):
    conn.execute("INSERT INTO Shop VALUES (?, ?, ?, ?)", ("1", "1001", "ShopA", "123456"))
    conn.commit()
    view = _view(membership_shop_config, conn)
    # rows = [section FIELDS(0), field creationDate(1),
    # section REFERENCED BY(2), group header(3), related shop1(4)].
    view.selected = 4

    transition = view.handle_key(keys.RETURN)

    assert not isinstance(transition.view, SelectionList)


def test_enter_on_local_column_with_exactly_one_match_opens_directly():
    # "id" is Membership's own primary key in membership_shop_config, so
    # it's a Referenced By relation, not a Reference (LocalColumnTarget)
    # row - there's no standalone row for it to select directly anymore.
    # This test now covers the equivalent case for an *outbound*
    # reference (this record holds the FK): selecting a Reference row
    # whose LocalColumnTarget has exactly one match opens it directly.
    order = Table(
        name="Order",
        columns=("id", "categoryRef"),
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
    config = Config(tables=MappingProxyType({"Order": order, "Category": category}))
    order_conn = sqlite3.connect(":memory:")
    order_conn.execute("CREATE TABLE Category (id TEXT, code TEXT, name TEXT)")
    order_conn.execute("INSERT INTO Category VALUES ('1', 'XYZ', 'CategoryA')")
    order_conn.commit()

    record = {"id": "99", "categoryRef": "XYZ"}
    view = TableView(order, record, order_conn, config, Breadcrumb())
    # rows = [section FIELDS(0), section REFERENCES(1),
    # reference categoryRef(2)].
    reference_index = next(
        i for i, r in enumerate(view.rows) if r.name.strip() == "categoryRef"
    )
    view.selected = reference_index

    transition = view.handle_key(keys.RETURN)

    assert isinstance(transition.view, TableView)
    assert transition.view.table.name == "Category"
    assert transition.view.record["id"] == "1"
    order_conn.close()


def test_enter_on_non_relation_row_does_nothing(membership_shop_config, conn):
    view = _view(membership_shop_config, conn)
    view.selected = 1  # creationDate, not a relation

    transition = view.handle_key(keys.RETURN)

    assert transition is None
