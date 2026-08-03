from dataclasses import dataclass
from typing import Any

from ..config.models import Table


@dataclass(frozen=True)
class Field:
    column: str
    value: str


@dataclass(frozen=True)
class RelationField(Field):
    related_table: str
    foreign_key_value: str


def build_fields(table: Table, row: dict[str, Any]) -> list[Field]:
    """Build one Field/RelationField per column, in Table.columns order (NFR3),
    with the table's "id" column always first even if columns omits it."""
    relations_by_local_column = {r.local_column: r for r in table.relations}
    if "id" in table.columns or "id" not in row:
        columns = table.columns
    else:
        columns = ("id", *table.columns)
    fields: list[Field] = []
    for column in columns:
        raw_value = row[column]
        relation = relations_by_local_column.get(column)
        if relation is None:
            fields.append(Field(column=column, value=str(raw_value)))
        else:
            fields.append(
                RelationField(
                    column=column,
                    value=f"{relation.target_table}[{raw_value}]",
                    related_table=relation.target_table,
                    foreign_key_value=str(raw_value),
                )
            )
    return fields
