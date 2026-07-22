import pytest

from dbbro.db.database_config import resolve_database_config
from dbbro.db.errors import DatabaseConfigError


def test_resolve_database_config_raises_when_host_is_not_a_string():
    raw = {"connections": {"prod": {"host": 12345, "name": "n", "user": "u", "password": "p"}}}

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={})


def test_resolve_database_config_malformed_and_missing_report_via_same_error_type():
    malformed = {"connections": {"prod": {"host": 12345, "name": "n", "user": "u", "password": "p"}}}
    missing = {"connections": {"prod": {"name": "n", "user": "u", "password": "p"}}}

    with pytest.raises(DatabaseConfigError) as malformed_exc:
        resolve_database_config(malformed, env={})
    with pytest.raises(DatabaseConfigError) as missing_exc:
        resolve_database_config(missing, env={})

    assert type(malformed_exc.value) is type(missing_exc.value)


def test_resolve_database_config_raises_when_alias_has_invalid_characters():
    raw = {
        "connections": {
            "my-db": {"host": "h", "name": "n", "user": "u", "password": "p"}
        }
    }

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={})
