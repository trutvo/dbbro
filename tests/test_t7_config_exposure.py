import dataclasses
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Table


def test_config_tables_are_immutable():
    config = Config(tables=MappingProxyType({}))

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.tables = MappingProxyType({"x": None})

    with pytest.raises(TypeError):
        config.tables["Company"] = None


def test_searchable_pairs_matches_declared_search_columns_exactly():
    tables = {
        "Company": Table(
            name="Company",
            columns=("id", "name", "uuid"),
            primary_key="id",
            search_columns=("name", "uuid"),
        ),
        "Membership": Table(
            name="Membership", columns=("id",), primary_key="id"
        ),
    }
    config = Config(tables=MappingProxyType(tables))

    assert set(config.searchable_pairs()) == {
        ("Company", "name"),
        ("Company", "uuid"),
    }


def test_table_with_empty_search_columns_contributes_nothing():
    tables = {
        "Membership": Table(name="Membership", columns=("id",), primary_key="id"),
    }
    config = Config(tables=MappingProxyType(tables))

    assert config.searchable_pairs() == []
