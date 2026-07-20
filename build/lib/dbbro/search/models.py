from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NoMatch:
    table: str
    column: str
    value: str


@dataclass(frozen=True)
class SingleMatch:
    table: str
    record: dict[str, Any]


@dataclass(frozen=True)
class MultipleMatches:
    table: str
    records: list[dict[str, Any]]


SearchOutcome = NoMatch | SingleMatch | MultipleMatches
