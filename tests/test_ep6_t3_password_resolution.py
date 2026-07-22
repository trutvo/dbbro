import pytest

from dbbro.db.database_config import resolve_database_config
from dbbro.db.errors import DatabaseConfigError


def _raw(password=None):
    db = {"host": "h", "name": "n", "user": "u"}
    if password is not None:
        db["password"] = password
    return {"connections": {"prod": db}}


def test_resolve_database_config_uses_file_password_when_present():
    config = resolve_database_config(_raw(password="filepass"), env={"DBBRO_DB_PWD_PROD": "envpass"})

    assert config.password == "filepass"


def test_resolve_database_config_ignores_env_var_when_file_password_present():
    config = resolve_database_config(_raw(password="filepass"), env={"DBBRO_DB_PWD_PROD": "shouldnotbeused"})

    assert config.password == "filepass"


def test_resolve_database_config_uses_env_var_when_file_password_absent():
    config = resolve_database_config(_raw(password=None), env={"DBBRO_DB_PWD_PROD": "envpass"})

    assert config.password == "envpass"


def test_resolve_database_config_raises_when_no_password_anywhere():
    with pytest.raises(DatabaseConfigError):
        resolve_database_config(_raw(password=None), env={})


def test_resolve_database_config_empty_string_env_var_treated_as_absent():
    with pytest.raises(DatabaseConfigError):
        resolve_database_config(_raw(password=None), env={"DBBRO_DB_PWD_PROD": ""})
