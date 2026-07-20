import sqlite3
from types import MappingProxyType

import pytest

from dbbro.config.models import Config, Table


@pytest.fixture
def two_table_config():
    company = Table(
        name="Company",
        columns=("id", "name"),
        primary_key="id",
        search_columns=("name",),
    )
    employee = Table(
        name="Employee",
        columns=("id", "name"),
        primary_key="id",
        search_columns=(),
    )
    return Config(tables=MappingProxyType({"Company": company, "Employee": employee}))


@pytest.fixture
def sqlite_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Company (id TEXT, name TEXT)")
    yield conn
    conn.close()
