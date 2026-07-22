import pytest

from dbbro.db.database_config import resolve_database_config
from dbbro.db.errors import DatabaseConfigError


def _raw(**connections):
    return {"tables": {}, "connections": connections}


def _conn(host="h", name="n", user="u", password="p"):
    return {"host": host, "name": name, "user": user, "password": password}


def test_single_connection_is_auto_selected_without_default_or_flag():
    raw = _raw(prod=_conn(name="proddb"))

    config = resolve_database_config(raw, env={})

    assert config.name == "proddb"


def test_default_key_selects_connection_when_no_flag_given():
    raw = _raw(prod=_conn(name="proddb"), staging=_conn(name="stagingdb"))
    raw["default"] = "staging"

    config = resolve_database_config(raw, env={})

    assert config.name == "stagingdb"


def test_connection_flag_overrides_default_key():
    raw = _raw(prod=_conn(name="proddb"), staging=_conn(name="stagingdb"))
    raw["default"] = "staging"

    config = resolve_database_config(raw, env={}, connection="prod")

    assert config.name == "proddb"


def test_raises_when_multiple_connections_and_no_default_or_flag():
    raw = _raw(prod=_conn(), staging=_conn())

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={})


def test_raises_when_default_references_unknown_alias():
    raw = _raw(prod=_conn())
    raw["default"] = "staging"

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={})


def test_raises_when_connection_flag_references_unknown_alias():
    raw = _raw(prod=_conn())

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={}, connection="staging")


def test_env_var_fallback_is_scoped_per_alias():
    raw = _raw(
        prod={"name": "proddb", "user": "u", "password": "p"},
        staging={"name": "stagingdb", "user": "u", "password": "p"},
    )

    config = resolve_database_config(
        raw,
        env={"DBBRO_DB_HOST_PROD": "prod-host", "DBBRO_DB_HOST_STAGING": "staging-host"},
        connection="staging",
    )

    assert config.host == "staging-host"
