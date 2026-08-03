from dbbro.config.models import Table
from dbbro.ui.relation_rows import format_record


def test_format_record_without_repr_falls_back_to_primary_key_value():
    table = Table(
        name="Shop",
        columns=("id", "tsId", "name"),
        primary_key="id",
        search_columns=("tsId", "name"),
    )
    record = {"id": "1", "tsId": "543334", "name": "Acme"}
    assert format_record(table, record) == "Shop[1]"


def test_format_record_uses_repr_template_when_configured():
    table = Table(
        name="PrimeProductItem",
        columns=("id", "product", "validFrom", "validTo"),
        primary_key="id",
        repr="{product} valid {validFrom} to {validTo}",
    )
    record = {
        "id": "1",
        "product": "SHOP_DOMAIN",
        "validFrom": "2025-08-11 14:02:44",
        "validTo": None,
    }
    result = format_record(table, record)
    assert result == "PrimeProductItem[SHOP_DOMAIN valid 2025-08-11 14:02:44 to None]"


def test_format_record_repr_treats_missing_key_as_none():
    table = Table(
        name="Shop",
        columns=("id", "tsId"),
        primary_key="id",
        repr="{tsId}",
    )
    record = {"id": "1"}
    assert format_record(table, record) == "Shop[None]"


def test_format_record_without_repr_single_column_uses_primary_key():
    table = Table(
        name="Membership",
        columns=("id", "name"),
        primary_key="id",
    )
    record = {"id": "123456", "name": "whatever"}
    assert format_record(table, record) == "Membership[123456]"
