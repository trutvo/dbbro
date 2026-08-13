from dbbro import cli


def test_ui_never_shown_when_config_invalid(tmp_path, monkeypatch, capsys):
    missing_path = tmp_path / "missing.yaml"
    connections_path = tmp_path / "connections.yaml"
    connections_path.write_text("connections: {prod: {host: h, name: n, user: u, password: p}}")
    called = []
    monkeypatch.setattr(
        cli, "run_ui", lambda config, conn, initial_outcome=None: called.append(config)
    )

    exit_code = cli.main(
        ["--config", str(missing_path), "--connections", str(connections_path)]
    )

    assert exit_code != 0
    assert called == []
    assert "not found" in capsys.readouterr().err


def test_ui_shown_after_valid_config_and_connection_succeed(tmp_path, monkeypatch):
    config_path = tmp_path / "good.yaml"
    config_path.write_text(
        """
tables:
  Company:
    columns: [id, name]
    primary_key: id
    search_columns: [name]
"""
    )
    connections_path = tmp_path / "connections.yaml"
    connections_path.write_text(
        """
connections:
  prod:
    host: db.example.com
    name: mydb
    user: dbbro
    password: secret
"""
    )
    called = []
    monkeypatch.setattr(
        cli,
        "run_ui",
        lambda config, conn, initial_outcome=None: called.append((config, conn)),
    )
    monkeypatch.setattr(cli, "connect", lambda db_config: "fake-connection")

    exit_code = cli.main(
        ["--config", str(config_path), "--connections", str(connections_path)]
    )

    assert exit_code == 0
    assert len(called) == 1
    config, conn = called[0]
    assert "Company" in config.tables
    assert conn == "fake-connection"


def test_inline_connections_in_schema_config_is_rejected(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "good.yaml"
    config_path.write_text(
        """
tables:
  Company:
    columns: [id, name]
    primary_key: id
connections:
  prod:
    host: db.example.com
    name: mydb
    user: dbbro
    password: secret
"""
    )
    connections_path = tmp_path / "connections.yaml"
    connections_path.write_text("connections: {prod: {host: h, name: n, user: u, password: p}}")
    called = []
    monkeypatch.setattr(
        cli, "run_ui", lambda config, conn, initial_outcome=None: called.append(config)
    )

    exit_code = cli.main(
        ["--config", str(config_path), "--connections", str(connections_path)]
    )

    assert exit_code != 0
    assert called == []
    assert "connections" in capsys.readouterr().err
