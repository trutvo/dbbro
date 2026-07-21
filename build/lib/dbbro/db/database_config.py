from typing import Mapping

from .errors import DatabaseConfigError
from .models import DatabaseConfig


def resolve_database_config(raw: dict, env: Mapping[str, str]) -> DatabaseConfig:
    """Reads raw['database'], resolves the password, and returns a
    DatabaseConfig, or raises DatabaseConfigError collecting every problem
    found in the section (missing section, missing/malformed required
    value, or no resolvable password)."""
    db_section = raw.get("database")
    if db_section is None:
        raise DatabaseConfigError(["database: section is missing"])

    issues: list[str] = []

    def _require_string(field: str):
        value = db_section.get(field)
        if value is None:
            issues.append(f"database.{field}: value is missing")
            return None
        if not isinstance(value, str):
            issues.append(f"database.{field}: value must be a string")
            return None
        return value

    file_host = db_section.get("host")
    if file_host is not None and not isinstance(file_host, str):
        issues.append("database.host: value must be a string")
        file_host = None

    host = file_host
    if not host:
        env_host = env.get("DBBRO_DB_HOST", "")
        host = env_host if env_host else None

    if host is None:
        issues.append(
            "database.host: no host available in the configuration "
            "file or the DBBRO_DB_HOST environment variable"
        )

    name = _require_string("name")
    user = _require_string("user")

    port = db_section.get("port")
    if port is not None and not isinstance(port, int):
        issues.append("database.port: value must be an integer")
        port = None

    file_password = db_section.get("password")
    if file_password is not None and not isinstance(file_password, str):
        issues.append("database.password: value must be a string")
        file_password = None

    password = file_password
    if not password:
        env_password = env.get("DBBRO_DB_PWD", "")
        password = env_password if env_password else None

    if password is None:
        issues.append(
            "database.password: no password available in the configuration "
            "file or the DBBRO_DB_PWD environment variable"
        )

    if issues:
        raise DatabaseConfigError(issues)

    return DatabaseConfig(host=host, name=name, user=user, password=password, port=port)
