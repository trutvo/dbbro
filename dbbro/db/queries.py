from typing import Any

from ..config.models import Table

Row = dict[str, Any]


def fetch_by_column_equals(conn, table: Table, column: str, value: str) -> list[Row]:
    columns_sql = ", ".join(table.columns)
    query = f"SELECT {columns_sql} FROM {table.name} WHERE {column} = ?"
    cursor = conn.execute(query, (value,))
    return [dict(zip(table.columns, row)) for row in cursor.fetchall()]


def fetch_by_primary_key(conn, table: Table, pk_value: str) -> Row | None:
    rows = fetch_by_column_equals(conn, table, table.primary_key, pk_value)
    return rows[0] if rows else None
