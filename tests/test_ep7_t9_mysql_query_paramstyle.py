from dbbro.config.models import Table
from dbbro.db.queries import fetch_by_column_equals


class _StubCursor:
    def __init__(self, rows):
        self._rows = rows
        self.executed = None

    def execute(self, query, params):
        self.executed = (query, params)

    def fetchall(self):
        return self._rows


class _StubMySQLConnection:
    """Mimics PyMySQL's Connection: has cursor(), no execute(), and (with
    DictCursor configured) returns dict rows from fetchall()."""

    def __init__(self, rows):
        self._cursor = _StubCursor(rows)

    def cursor(self):
        return self._cursor


def test_fetch_by_column_equals_uses_percent_s_placeholder_and_cursor_for_non_sqlite():
    table = Table(name="Company", columns=("id", "name"), primary_key="id")
    conn = _StubMySQLConnection(rows=[{"id": "1", "name": "Acme"}])

    result = fetch_by_column_equals(conn, table, "name", "Acme")

    assert result == [{"id": "1", "name": "Acme"}]
    query, params = conn._cursor.executed
    assert "%s" in query
    assert "?" not in query
    assert params == ("Acme",)
