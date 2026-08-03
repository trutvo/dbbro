import sqlite3
from typing import Any

import pymysql

from ..config.models import Table

Row = dict[str, Any]

# Raised by sqlite3/PyMySQL for "no such column" style failures.
_UNKNOWN_COLUMN_ERRORS = (sqlite3.OperationalError, pymysql.MySQLError)


def fetch_by_column_equals(conn, table: Table, column: str, value: str) -> list[Row]:
    is_sqlite = isinstance(conn, sqlite3.Connection)
    placeholder = "?" if is_sqlite else "%s"
    try:
        return _select(conn, table, column, value, placeholder, is_sqlite, include_id=True)
    except _UNKNOWN_COLUMN_ERRORS:
        # This table's DB schema has no "id" column at all - fall back to
        # just its declared columns.
        return _select(conn, table, column, value, placeholder, is_sqlite, include_id=False)


def _select(
    conn, table: Table, column: str, value: str, placeholder: str, is_sqlite: bool, include_id: bool
) -> list[Row]:
    if include_id:
        select_columns = ("id", *(c for c in table.columns if c != "id"))
    else:
        select_columns = table.columns
    columns_sql = ", ".join(select_columns)
    query = f"SELECT {columns_sql} FROM {table.name} WHERE {column} = {placeholder}"
    cursor = conn.cursor()
    cursor.execute(query, (value,))
    rows = cursor.fetchall()
    if is_sqlite:
        return [dict(zip(select_columns, row)) for row in rows]
    # PyMySQL's connection is configured with DictCursor (see connection.py),
    # so rows already come back as dicts keyed by column name.
    return [dict(row) for row in rows]


def fetch_by_primary_key(conn, table: Table, pk_value: str) -> Row | None:
    rows = fetch_by_column_equals(conn, table, table.primary_key, pk_value)
    return rows[0] if rows else None
