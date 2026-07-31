from dbbro.config.models import Table
from dbbro.ui.relation_rows import format_record


def test_format_record_renders_all_columns_as_key_value_pairs_in_declared_order():
    table = Table(
        name="Shop",
        columns=("id", "tsId", "name"),
        primary_key="id",
        search_columns=("tsId", "name"),
    )
    record = {"id": "1", "tsId": "543334", "name": "Acme"}
    assert format_record(table, record) == "id=1, tsId=543334, name=Acme"


def test_format_record_ignores_search_columns_and_includes_every_column():
    table = Table(
        name="Shop",
        columns=("id", "tsId", "name", "url"),
        primary_key="id",
        search_columns=("tsId",),
    )
    record = {"id": "1", "tsId": "543334", "name": "Acme", "url": "http://x"}
    result = format_record(table, record)
    assert result == "id=1, tsId=543334, name=Acme, url=http://x"
    for column in table.columns:
        assert f"{column}=" in result


def test_format_record_single_column_returns_key_value_pair():
    table = Table(
        name="Shop",
        columns=("id", "tsId"),
        primary_key="id",
        search_columns=("tsId",),
    )
    record = {"id": "1", "tsId": "543334"}
    assert format_record(table, record) == "id=1, tsId=543334"


def test_format_record_works_when_search_columns_empty():
    table = Table(
        name="Membership",
        columns=("id", "name"),
        primary_key="id",
        search_columns=(),
    )
    record = {"id": "123456", "name": "whatever"}
    assert format_record(table, record) == "id=123456, name=whatever"
