from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigIssue:
    message: str
    table: str | None = None
    column: str | None = None
    relation_label: str | None = None

    def __str__(self) -> str:
        if self.relation_label is not None:
            return f"relation '{self.relation_label}': {self.message}"
        if self.table is not None and self.column is not None:
            return f"{self.table}.{self.column}: {self.message}"
        if self.table is not None:
            return f"{self.table}: {self.message}"
        return self.message


class ConfigValidationError(Exception):
    def __init__(self, issues: list[ConfigIssue]):
        self.issues = issues
        super().__init__("\n".join(str(issue) for issue in issues))
