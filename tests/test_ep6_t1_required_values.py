import pytest

from dbbro.db.database_config import resolve_database_config
from dbbro.db.errors import DatabaseConfigError


def _raw(database=None):
    raw = {"tables": {}}
    if database is not None:
        raw["database"] = database
    return raw


def test_resolve_database_config_returns_config_for_full_valid_section():
    raw = _raw({"host": "db.example.com", "name": "mydb", "user": "alice", "password": "s3cret"})

    config = resolve_database_config(raw, env={})

    assert config.host == "db.example.com"
    assert config.name == "mydb"
    assert config.user == "alice"
    assert config.password == "s3cret"
    assert config.port is None


def test_resolve_database_config_accepts_missing_password_in_shape():
    raw = _raw({"host": "db.example.com", "name": "mydb", "user": "alice"})

    config = resolve_database_config(raw, env={"DBBRO_DB_PWD": "envpass"})

    assert config.password == "envpass"


def test_resolve_database_config_raises_when_database_section_absent():
    raw = _raw(database=None)

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={})


def test_resolve_database_config_raises_when_host_missing():
    raw = _raw({"name": "mydb", "user": "alice", "password": "x"})

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={})


def test_resolve_database_config_raises_when_name_missing():
    raw = _raw({"host": "h", "user": "alice", "password": "x"})

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={})


def test_resolve_database_config_raises_when_user_missing():
    raw = _raw({"host": "h", "name": "mydb", "password": "x"})

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={})


def test_resolve_database_config_uses_given_port_when_present():
    raw = _raw({"host": "h", "name": "n", "user": "u", "password": "p", "port": 5432})

    config = resolve_database_config(raw, env={})

    assert config.port == 5432


def test_resolve_database_config_port_is_none_when_absent():
    raw = _raw({"host": "h", "name": "n", "user": "u", "password": "p"})

    config = resolve_database_config(raw, env={})

    assert config.port is None
