import sqlite3
from typing import Any

from ..config.models import Table

Row = dict[str, Any]


def fetch_by_column_equals(conn, table: Table, column: str, value: str) -> list[Row]:
    is_sqlite = isinstance(conn, sqlite3.Connection)
    placeholder = "?" if is_sqlite else "%s"
    columns_sql = ", ".join(table.columns)
    query = f"SELECT {columns_sql} FROM {table.name} WHERE {column} = {placeholder}"
    cursor = conn.cursor()
    cursor.execute(query, (value,))
    rows = cursor.fetchall()
    if is_sqlite:
        return [dict(zip(table.columns, row)) for row in rows]
    # PyMySQL's connection is configured with DictCursor (see connection.py),
    # so rows already come back as dicts keyed by column name.
    return [dict(row) for row in rows]


def fetch_by_primary_key(conn, table: Table, pk_value: str) -> Row | None:
    rows = fetch_by_column_equals(conn, table, table.primary_key, pk_value)
    return rows[0] if rows else None
