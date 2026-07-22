import sqlite3
from types import MappingProxyType

import pytest

from dbbro import cli
from dbbro.cli import QuickSearchError, parse_quick_search, resolve_quick_search
from dbbro.config.models import Config, Table
from dbbro.search.models import MultipleMatches, SingleMatch


@pytest.fixture
def qs_config():
    company = Table(
        name="Company",
        columns=("id", "uuid", "name"),
        primary_key="id",
        search_columns=("uuid", "name"),
    )
    return Config(tables=MappingProxyType({"Company": company}))


@pytest.fixture
def qs_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE Company (id TEXT, uuid TEXT, name TEXT)")
    yield conn
    conn.close()


# --- parse_quick_search -----------------------------------------------------


def test_parse_quick_search_splits_table_column_value():
    assert parse_quick_search("Company.uuid=abc123") == ("Company", "uuid", "abc123")


def test_parse_quick_search_value_may_contain_equals_signs():
    assert parse_quick_search("Company.uuid=a=b=c") == ("Company", "uuid", "a=b=c")


def test_parse_quick_search_raises_when_equals_missing():
    with pytest.raises(QuickSearchError):
        parse_quick_search("Company.uuid")


def test_parse_quick_search_raises_when_dot_missing():
    with pytest.raises(QuickSearchError):
        parse_quick_search("Companyuuid=abc")


def test_parse_quick_search_raises_when_value_empty():
    with pytest.raises(QuickSearchError):
        parse_quick_search("Company.uuid=")


def test_parse_quick_search_raises_when_table_or_column_empty():
    with pytest.raises(QuickSearchError):
        parse_quick_search(".uuid=abc")
    with pytest.raises(QuickSearchError):
        parse_quick_search("Company.=abc")


# --- resolve_quick_search ----------------------------------------------------


def test_resolve_quick_search_raises_for_non_searchable_column(qs_config, qs_conn):
    with pytest.raises(QuickSearchError):
        resolve_quick_search("Company.id=1", qs_config, qs_conn)


def test_resolve_quick_search_raises_for_unknown_table(qs_config, qs_conn):
    with pytest.raises(QuickSearchError):
        resolve_quick_search("Unknown.uuid=1", qs_config, qs_conn)


def test_resolve_quick_search_raises_on_zero_matches(qs_config, qs_conn):
    with pytest.raises(QuickSearchError):
        resolve_quick_search("Company.uuid=nope", qs_config, qs_conn)


def test_resolve_quick_search_returns_single_match(qs_config, qs_conn):
    qs_conn.execute("INSERT INTO Company VALUES ('1', 'abc', 'Acme')")

    outcome = resolve_quick_search("Company.uuid=abc", qs_config, qs_conn)

    assert isinstance(outcome, SingleMatch)
    assert outcome.record["name"] == "Acme"


def test_resolve_quick_search_returns_multiple_matches(qs_config, qs_conn):
    qs_conn.execute("INSERT INTO Company VALUES ('1', 'x', 'Acme')")
    qs_conn.execute("INSERT INTO Company VALUES ('2', 'x', 'Beta')")

    outcome = resolve_quick_search("Company.uuid=x", qs_config, qs_conn)

    assert isinstance(outcome, MultipleMatches)
    assert len(outcome.records) == 2


# --- main() wiring ------------------------------------------------------------


def _write_config(tmp_path):
    config_path = tmp_path / "cfg.yaml"
    config_path.write_text(
        """
tables:
  Company:
    columns: [id, uuid, name]
    primary_key: id
    search_columns: [uuid]
connections:
  prod:
    host: h
    name: n
    user: u
    password: p
"""
    )
    return config_path


def test_main_reports_error_and_exits_nonzero_for_invalid_search(tmp_path, monkeypatch, capsys):
    config_path = _write_config(tmp_path)
    monkeypatch.setattr(cli, "connect", lambda db_config: object())
    monkeypatch.setattr(
        cli, "find_matches", lambda conn, table, column, value: __import__("dbbro.search.models", fromlist=["NoMatch"]).NoMatch(table.name, column, value)
    )

    exit_code = cli.main(["--config", str(config_path), "--search", "Company.uuid=nope"])

    assert exit_code != 0
    assert "no record found" in capsys.readouterr().err


def test_main_passes_initial_outcome_to_run_ui_on_match(tmp_path, monkeypatch):
    from dbbro.search.models import SingleMatch

    config_path = _write_config(tmp_path)
    monkeypatch.setattr(cli, "connect", lambda db_config: object())
    fake_outcome = SingleMatch(table="Company", record={"id": "1", "uuid": "abc", "name": "Acme"})
    monkeypatch.setattr(
        cli, "find_matches", lambda conn, table, column, value: fake_outcome
    )
    called = []
    monkeypatch.setattr(
        cli,
        "run_ui",
        lambda config, conn, initial_outcome=None: called.append(initial_outcome),
    )

    exit_code = cli.main(["--config", str(config_path), "--search", "Company.uuid=abc"])

    assert exit_code == 0
    assert called == [fake_outcome]


def test_main_without_search_flag_passes_no_initial_outcome(tmp_path, monkeypatch):
    config_path = _write_config(tmp_path)
    monkeypatch.setattr(cli, "connect", lambda db_config: object())
    called = []
    monkeypatch.setattr(
        cli,
        "run_ui",
        lambda config, conn, initial_outcome=None: called.append(initial_outcome),
    )

    exit_code = cli.main(["--config", str(config_path)])

    assert exit_code == 0
    assert called == [None]
