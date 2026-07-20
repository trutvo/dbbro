class DatabaseConfigError(Exception):
    """One or more problems with the `database` config section itself
    (missing section, missing/malformed value, unresolvable password)."""

    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("\n".join(issues))


class DatabaseConnectionError(Exception):
    """The database could not be reached or rejected the credentials.
    Message never includes the password."""
