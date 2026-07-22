import pymysql
import pytest

from dbbro import cli
from dbbro.db.connection import connect
from dbbro.db.errors import DatabaseConfigError, DatabaseConnectionError
from dbbro.db.models import DatabaseConfig


def _write_good_config(tmp_path, database_yaml):
    config_path = tmp_path / "cfg.yaml"
    config_path.write_text(
        f"""
tables:
  Company:
    columns: [id, name]
    primary_key: id
    search_columns: [name]
{database_yaml}
"""
    )
    return config_path


def test_main_reports_database_config_error_and_exits_nonzero(tmp_path, capsys):
    config_path = _write_good_config(
        tmp_path, "connections:\n  prod:\n    host: h\n"
    )

    exit_code = cli.main(["--config", str(config_path)])

    assert exit_code != 0
    assert capsys.readouterr().err.strip() != ""


def test_main_reports_database_connection_error_and_exits_nonzero(
    tmp_path, monkeypatch, capsys
):
    config_path = _write_good_config(
        tmp_path,
        "connections:\n  prod:\n    host: h\n    name: n\n    user: u\n    password: p\n",
    )
    monkeypatch.setattr(
        cli,
        "connect",
        lambda db_config: (_ for _ in ()).throw(DatabaseConnectionError("boom")),
    )

    exit_code = cli.main(["--config", str(config_path)])

    assert exit_code != 0
    assert "boom" in capsys.readouterr().err


def test_database_config_error_message_never_contains_the_password_value():
    from dbbro.db.database_config import resolve_database_config

    raw = {"connections": {"prod": {"host": "h", "user": "u"}}}
    with pytest.raises(DatabaseConfigError) as exc:
        resolve_database_config(raw, env={})

    assert "hunter2" not in str(exc.value)


def test_database_connection_error_message_never_contains_the_password_value(
    monkeypatch,
):
    def fake_connect(**kwargs):
        raise pymysql.MySQLError("auth failed for hunter2")

    monkeypatch.setattr(pymysql, "connect", fake_connect)
    config = DatabaseConfig(host="h", name="n", user="u", password="hunter2")

    with pytest.raises(DatabaseConnectionError) as exc:
        connect(config)

    assert "hunter2" not in str(exc.value)
