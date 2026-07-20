from dbbro.config.models import Table
from dbbro.search.lookup import find_matches
from dbbro.search.models import MultipleMatches, NoMatch, SingleMatch

COMPANY = Table(name="Company", columns=("id", "name"), primary_key="id")


def test_find_matches_returns_single_match_for_one_row(sqlite_conn):
    sqlite_conn.execute("INSERT INTO Company VALUES ('1', 'Acme')")

    outcome = find_matches(sqlite_conn, COMPANY, "name", "Acme")

    assert isinstance(outcome, SingleMatch)
    assert outcome.record == {"id": "1", "name": "Acme"}


def test_find_matches_returns_multiple_matches_for_several_rows(sqlite_conn):
    sqlite_conn.execute("INSERT INTO Company VALUES ('1', 'Acme')")
    sqlite_conn.execute("INSERT INTO Company VALUES ('2', 'Acme')")

    outcome = find_matches(sqlite_conn, COMPANY, "name", "Acme")

    assert isinstance(outcome, MultipleMatches)
    assert len(outcome.records) == 2


def test_find_matches_returns_no_match_naming_table_column_value(sqlite_conn):
    outcome = find_matches(sqlite_conn, COMPANY, "name", "Nope")

    assert outcome == NoMatch(table="Company", column="name", value="Nope")


def test_find_matches_uses_exact_match_not_substring(sqlite_conn):
    sqlite_conn.execute("INSERT INTO Company VALUES ('1', 'Acme Inc')")

    outcome = find_matches(sqlite_conn, COMPANY, "name", "Acme")

    assert isinstance(outcome, NoMatch)
