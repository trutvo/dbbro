from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class Relation:
    target_table: str
    local_column: str
    foreign_column: str
    label: str


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[str, ...]
    primary_key: str
    search_columns: tuple[str, ...] = ()
    relations: tuple[Relation, ...] = ()


@dataclass(frozen=True)
class Config:
    tables: MappingProxyType[str, Table]

    def searchable_pairs(self) -> list[tuple[str, str]]:
        return [
            (table.name, column)
            for table in self.tables.values()
            for column in table.search_columns
        ]
