from types import MappingProxyType

from .errors import ConfigIssue, ConfigValidationError
from .models import Config, Relation, Table


def validate_tables(raw: dict) -> list[ConfigIssue]:
    issues: list[ConfigIssue] = []
    raw_tables = raw.get("tables") or {}

    for name, table_def in raw_tables.items():
        columns = list(table_def.get("columns") or [])
        if not columns:
            issues.append(
                ConfigIssue(table=name, message="table has no columns")
            )

        seen_columns: set[str] = set()
        for column in columns:
            if column in seen_columns:
                issues.append(
                    ConfigIssue(
                        table=name, column=column, message="duplicate column name"
                    )
                )
            seen_columns.add(column)

        primary_key = table_def.get("primary_key")
        if primary_key not in columns:
            issues.append(
                ConfigIssue(
                    table=name,
                    column=primary_key,
                    message="primary key is not a declared column",
                )
            )

        search_columns = list(table_def.get("search_columns") or [])
        for column in search_columns:
            if column not in columns:
                issues.append(
                    ConfigIssue(
                        table=name,
                        column=column,
                        message="search column is not a declared column",
                    )
                )

    return issues


def validate_relations(raw: dict) -> list[ConfigIssue]:
    issues: list[ConfigIssue] = []
    raw_tables = raw.get("tables") or {}
    seen_labels: dict[str, str] = {}

    for name, table_def in raw_tables.items():
        columns = list(table_def.get("columns") or [])
        relations = table_def.get("relations") or []

        for relation_def in relations:
            label = relation_def.get("label")
            target_table = relation_def.get("table")
            local_column = relation_def.get("local_column")
            foreign_column = relation_def.get("foreign_column")

            if label in seen_labels:
                issues.append(
                    ConfigIssue(
                        relation_label=label,
                        message=(
                            "relation label is used by more than one relation "
                            f"(also declared on table '{seen_labels[label]}')"
                        ),
                    )
                )
            else:
                seen_labels[label] = name

            if target_table not in raw_tables:
                issues.append(
                    ConfigIssue(
                        relation_label=label,
                        message=f"relation targets undeclared table '{target_table}'",
                    )
                )

            if local_column not in columns:
                issues.append(
                    ConfigIssue(
                        relation_label=label,
                        message=(
                            f"relation's local column '{local_column}' is not a "
                            f"declared column of table '{name}'"
                        ),
                    )
                )

            if target_table in raw_tables:
                target_columns = list(raw_tables[target_table].get("columns") or [])
                if foreign_column not in target_columns:
                    issues.append(
                        ConfigIssue(
                            relation_label=label,
                            message=(
                                f"relation's foreign column '{foreign_column}' is not "
                                f"a declared column of table '{target_table}'"
                            ),
                        )
                    )

    return issues


def _build_config(raw: dict) -> Config:
    raw_tables = raw.get("tables") or {}
    tables = {}
    for name, table_def in raw_tables.items():
        relations = tuple(
            Relation(
                target_table=r.get("table"),
                local_column=r.get("local_column"),
                foreign_column=r.get("foreign_column"),
                label=r.get("label"),
            )
            for r in (table_def.get("relations") or [])
        )
        tables[name] = Table(
            name=name,
            columns=tuple(table_def.get("columns") or []),
            primary_key=table_def.get("primary_key"),
            search_columns=tuple(table_def.get("search_columns") or []),
            relations=relations,
        )
    return Config(tables=MappingProxyType(tables))


def validate_config(raw: dict) -> Config:
    issues = validate_tables(raw) + validate_relations(raw)
    if issues:
        raise ConfigValidationError(issues)
    return _build_config(raw)
