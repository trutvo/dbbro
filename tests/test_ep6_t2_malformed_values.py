import pytest

from dbbro.db.database_config import resolve_database_config
from dbbro.db.errors import DatabaseConfigError


def test_resolve_database_config_raises_when_host_is_not_a_string():
    raw = {"database": {"host": 12345, "name": "n", "user": "u", "password": "p"}}

    with pytest.raises(DatabaseConfigError):
        resolve_database_config(raw, env={})


def test_resolve_database_config_malformed_and_missing_report_via_same_error_type():
    malformed = {"database": {"host": 12345, "name": "n", "user": "u", "password": "p"}}
    missing = {"database": {"name": "n", "user": "u", "password": "p"}}

    with pytest.raises(DatabaseConfigError) as malformed_exc:
        resolve_database_config(malformed, env={})
    with pytest.raises(DatabaseConfigError) as missing_exc:
        resolve_database_config(missing, env={})

    assert type(malformed_exc.value) is type(missing_exc.value)
