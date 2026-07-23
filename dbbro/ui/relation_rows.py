from dataclasses import dataclass
from typing import Any

from ..config.models import Config, Table
from ..db.queries import fetch_by_column_equals
from .fields import Field, RelationField


@dataclass(frozen=True)
class LocalColumnTarget:
    target_table: str
    matches: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class RelatedEntityTarget:
    target_table: str
    record: dict[str, Any]


RowTarget = LocalColumnTarget | RelatedEntityTarget | None


def identifying_value(table: Table, record: dict[str, Any]) -> str:
    """Concatenates `table.search_columns` values, space-separated, in
    declared order. If `table.search_columns` is empty, falls back to the
    value of `table.columns[0]` (F9/AC10)."""
    columns = table.search_columns if table.search_columns else (table.columns[0],)
    return " ".join(str(record[column]) for column in columns)


def build_display_rows(
    fields: list[Field],
    table: Table,
    config: Config,
    conn,
) -> tuple[list[tuple[str, str]], list[RowTarget]]:
    """Expands one row per plain Field (target None), and (local-column row
    + one row per matched related entity per relation, in table.relations
    order) per RelationField. The local-column row's target reflects only
    the first configured relation for that column (D1); each related-entity
    row's target reflects its own relation and matched record."""
    rows: list[tuple[str, str]] = []
    row_targets: list[RowTarget] = []
    for field in fields:
        if not isinstance(field, RelationField):
            rows.append((field.column, field.value))
            row_targets.append(None)
            continue

        column_relations = [r for r in table.relations if r.local_column == field.column]
        first_relation = column_relations[0]
        matches_by_relation: dict[int, list[dict[str, Any]]] = {}

        for i, relation in enumerate(column_relations):
            target_table = config.tables[relation.target_table]
            matches = fetch_by_column_equals(
                conn, target_table, relation.foreign_column, field.foreign_key_value
            )
            matches_by_relation[i] = matches

        rows.append((field.column, field.foreign_key_value))
        row_targets.append(
            LocalColumnTarget(
                target_table=first_relation.target_table,
                matches=tuple(matches_by_relation[0]),
            )
        )

        for i, relation in enumerate(column_relations):
            target_table = config.tables[relation.target_table]
            for match in matches_by_relation[i]:
                value = f"=> {relation.target_table}[{identifying_value(target_table, match)}]"
                rows.append(("", value))
                row_targets.append(
                    RelatedEntityTarget(target_table=relation.target_table, record=match)
                )
    return rows, row_targets
