from dataclasses import dataclass
from typing import Any, Literal

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

RowKind = Literal["section", "group", "field", "reference", "related"]

INDENT = "  "


@dataclass(frozen=True)
class DisplayRow:
    """A single displayable row. "field" and "reference" rows use the
    two-column name/value layout; "section", "group", and "related" rows
    render full-width, with their text held in `value` (name unused)."""

    name: str
    value: str
    kind: RowKind

    @property
    def selectable(self) -> bool:
        return self.kind in ("field", "reference", "related")


def format_record(table: Table, record: dict[str, Any]) -> str:
    """Renders every column of `table.columns`, in declared order, as
    `column=value` pairs joined by ", "."""
    return ", ".join(f"{column}={record[column]}" for column in table.columns)


def build_display_rows(
    fields: list[Field],
    table: Table,
    config: Config,
    conn,
) -> tuple[list[DisplayRow], list[RowTarget]]:
    """Splits fields into three sections, each rendered only if non-empty:
    Fields (plain columns, two-column layout, titled with the table's own
    name instead of a generic label), references (this record's own FK
    columns, two-column layout), and referenced by (other tables' records
    pointing at this one, grouped by relation type, full-width rows, in
    table.relations declaration order). A relation is classified as
    referenced by when it's keyed off the table's primary key (other tables
    hold the FK pointing at us) and as a reference otherwise (this table
    holds the FK). Rows are indented by depth to read as a tree nested under
    the table-name section (depth 0, whose title is drawn by draw_panel as
    that section's own box border): section headers at depth 1 (one INDENT),
    field/reference/group rows at depth 2 (two INDENTs), related-record rows
    at depth 3 (three INDENTs)."""
    field_rows: list[DisplayRow] = []
    field_targets: list[RowTarget] = []
    reference_rows: list[DisplayRow] = []
    reference_targets: list[RowTarget] = []
    referenced_by_groups: list[tuple[str, list[DisplayRow], list[RowTarget]]] = []

    for field in fields:
        if not isinstance(field, RelationField):
            field_rows.append(DisplayRow(INDENT * 2 + field.column, field.value, "field"))
            field_targets.append(None)
            continue

        column_relations = [r for r in table.relations if r.local_column == field.column]
        is_referenced_by = field.column == table.primary_key

        matches_by_relation: dict[int, list[dict[str, Any]]] = {}
        for i, relation in enumerate(column_relations):
            target_table = config.tables[relation.target_table]
            matches_by_relation[i] = fetch_by_column_equals(
                conn, target_table, relation.foreign_column, field.foreign_key_value
            )

        if not is_referenced_by:
            first_relation = column_relations[0]
            reference_rows.append(DisplayRow(INDENT * 2 + field.column, field.value, "reference"))
            reference_targets.append(
                LocalColumnTarget(
                    target_table=first_relation.target_table,
                    matches=tuple(matches_by_relation[0]),
                )
            )
            continue

        for i, relation in enumerate(column_relations):
            target_table = config.tables[relation.target_table]
            matches = matches_by_relation[i]
            if not matches:
                continue
            label = f"{relation.target_table}.{relation.foreign_column}"
            group_rows: list[DisplayRow] = []
            group_targets: list[RowTarget] = []
            for match in matches:
                value = format_record(target_table, match)
                group_rows.append(DisplayRow("", INDENT * 3 + value, "related"))
                group_targets.append(
                    RelatedEntityTarget(target_table=relation.target_table, record=match)
                )
            referenced_by_groups.append((label, group_rows, group_targets))

    rows: list[DisplayRow] = []
    targets: list[RowTarget] = []

    if field_rows:
        rows.append(DisplayRow("", f"{INDENT}{table.name}", "section"))
        targets.append(None)
        rows.extend(field_rows)
        targets.extend(field_targets)

    if reference_rows:
        rows.append(DisplayRow("", f"{INDENT}references", "section"))
        targets.append(None)
        rows.extend(reference_rows)
        targets.extend(reference_targets)

    if referenced_by_groups:
        rows.append(DisplayRow("", f"{INDENT}referenced by", "section"))
        targets.append(None)
        for label, group_rows, group_targets in referenced_by_groups:
            rows.append(DisplayRow("", f"{INDENT * 2}{label} ({len(group_rows)})", "group"))
            targets.append(None)
            rows.extend(group_rows)
            targets.extend(group_targets)

    return rows, targets
