from dataclasses import dataclass
from typing import Any

from ..config.models import Table


@dataclass(frozen=True)
class Field:
    column: str
    value: str


@dataclass(frozen=True)
class RelationField(Field):
    label: str
    related_table: str
    foreign_key_value: str


def build_fields(table: Table, row: dict[str, Any]) -> list[Field]:
    """Build one Field/RelationField per column, in Table.columns order (NFR3)."""
    relations_by_local_column = {r.local_column: r for r in table.relations}
    fields: list[Field] = []
    for column in table.columns:
        raw_value = row[column]
        relation = relations_by_local_column.get(column)
        if relation is None:
            fields.append(Field(column=column, value=str(raw_value)))
        else:
            fields.append(
                RelationField(
                    column=column,
                    value=f"{relation.target_table}[{raw_value}]",
                    label=relation.label,
                    related_table=relation.target_table,
                    foreign_key_value=str(raw_value),
                )
            )
    return fields
