from ..config.models import Table
from ..db.queries import fetch_by_column_equals
from .models import MultipleMatches, NoMatch, SearchOutcome, SingleMatch


def find_matches(conn, table: Table, column: str, value: str) -> SearchOutcome:
    """Exact-match lookup of `value` in `table.column`.

    Returns NoMatch, SingleMatch, or MultipleMatches depending on the
    number of rows found. Raises no exception for zero matches — that is
    a normal SearchOutcome, not a failure of this function.
    """
    records = fetch_by_column_equals(conn, table, column, value)
    if not records:
        return NoMatch(table=table.name, column=column, value=value)
    if len(records) == 1:
        return SingleMatch(table=table.name, record=records[0])
    return MultipleMatches(table=table.name, records=records)
