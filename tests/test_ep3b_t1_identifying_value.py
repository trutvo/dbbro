from dbbro.config.models import Table
from dbbro.ui.relation_rows import identifying_value


def test_identifying_value_concatenates_search_columns_in_order():
    table = Table(
        name="Shop",
        columns=("id", "tsId", "name"),
        primary_key="id",
        search_columns=("tsId", "name"),
    )
    record = {"id": "1", "tsId": "543334", "name": "Acme"}
    assert identifying_value(table, record) == "543334 Acme"


def test_identifying_value_uses_only_declared_search_columns():
    table = Table(
        name="Shop",
        columns=("id", "tsId", "name", "url"),
        primary_key="id",
        search_columns=("tsId",),
    )
    record = {"id": "1", "tsId": "543334", "name": "Acme", "url": "http://x"}
    assert identifying_value(table, record) == "543334"


def test_identifying_value_single_search_column_returns_bare_value():
    table = Table(
        name="Shop",
        columns=("id", "tsId"),
        primary_key="id",
        search_columns=("tsId",),
    )
    record = {"id": "1", "tsId": "543334"}
    assert identifying_value(table, record) == "543334"


def test_identifying_value_falls_back_to_first_column_when_search_columns_empty():
    table = Table(
        name="Membership",
        columns=("id", "name"),
        primary_key="id",
        search_columns=(),
    )
    record = {"id": "123456", "name": "whatever"}
    assert identifying_value(table, record) == "123456"
