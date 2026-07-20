from dbbro import cli


def test_main_does_not_call_resolve_database_config_when_schema_validation_fails(
    tmp_path, monkeypatch
):
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(
        """
tables:
  Company:
    columns: []
    primary_key: id
"""
    )
    called = []
    monkeypatch.setattr(
        cli, "resolve_database_config", lambda raw, env: called.append(1)
    )

    exit_code = cli.main(["--config", str(config_path)])

    assert exit_code != 0
    assert called == []


def test_main_calls_resolve_database_config_only_after_schema_validation_succeeds(
    tmp_path, monkeypatch
):
    config_path = tmp_path / "good.yaml"
    config_path.write_text(
        """
tables:
  Company:
    columns: [id, name]
    primary_key: id
    search_columns: [name]
database:
  host: h
  name: n
  user: u
  password: p
"""
    )
    called = []
    monkeypatch.setattr(
        cli,
        "resolve_database_config",
        lambda raw, env: called.append(1) or _fake_config(),
    )
    monkeypatch.setattr(cli, "connect", lambda db_config: "fake-connection")
    monkeypatch.setattr(cli, "run_ui", lambda config, conn, initial_outcome=None: None)

    exit_code = cli.main(["--config", str(config_path)])

    assert exit_code == 0
    assert called == [1]


def _fake_config():
    from dbbro.db.models import DatabaseConfig

    return DatabaseConfig(host="h", name="n", user="u", password="p")
