from dbbro.config.models import Table
from dbbro.db.queries import fetch_by_column_equals, fetch_by_primary_key

COMPANY = Table(name="Company", columns=("id", "name"), primary_key="id")


def test_fetch_by_primary_key_returns_row_when_found(sqlite_conn):
    sqlite_conn.execute("INSERT INTO Company VALUES ('1', 'Acme')")

    row = fetch_by_primary_key(sqlite_conn, COMPANY, "1")

    assert row == {"id": "1", "name": "Acme"}


def test_fetch_by_primary_key_returns_none_when_missing(sqlite_conn):
    assert fetch_by_primary_key(sqlite_conn, COMPANY, "missing") is None


def test_fetch_by_column_equals_returns_all_matching_rows(sqlite_conn):
    sqlite_conn.execute("INSERT INTO Company VALUES ('1', 'Acme')")
    sqlite_conn.execute("INSERT INTO Company VALUES ('2', 'Acme')")

    rows = fetch_by_column_equals(sqlite_conn, COMPANY, "name", "Acme")

    assert len(rows) == 2


def test_fetch_by_column_equals_returns_empty_list_when_no_match(sqlite_conn):
    assert fetch_by_column_equals(sqlite_conn, COMPANY, "name", "Nope") == []
