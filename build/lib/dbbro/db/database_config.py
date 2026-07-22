import re
from typing import Mapping

from .errors import DatabaseConfigError
from .models import DatabaseConfig

ALIAS_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def resolve_database_config(
    raw: dict, env: Mapping[str, str], connection: str | None = None
) -> DatabaseConfig:
    """Reads raw['connections'], picks the connection named by `connection`
    (falling back to raw['default'], then to the sole entry if there's only
    one), resolves its password/host, and returns a DatabaseConfig. Raises
    DatabaseConfigError collecting every problem found (missing/empty
    connections section, invalid alias, unresolvable selection, missing or
    malformed required value, or no resolvable password)."""
    connections_section = raw.get("connections")
    if not connections_section:
        raise DatabaseConfigError(["connections: section is missing or empty"])

    for alias in connections_section:
        if not ALIAS_PATTERN.match(alias):
            raise DatabaseConfigError(
                [f"connections.{alias}: alias must match ^[a-zA-Z0-9_]+$"]
            )

    default_alias = raw.get("default")
    if default_alias is not None and default_alias not in connections_section:
        raise DatabaseConfigError(
            [f"default: '{default_alias}' does not match any connection alias"]
        )

    if connection is not None:
        alias = connection
    elif default_alias is not None:
        alias = default_alias
    elif len(connections_section) == 1:
        alias = next(iter(connections_section))
    else:
        raise DatabaseConfigError(
            [
                "connections: multiple connections declared; specify "
                "--connection or a 'default' alias"
            ]
        )

    if alias not in connections_section:
        raise DatabaseConfigError(
            [f"--connection: '{alias}' does not match any connection alias"]
        )

    db_section = connections_section[alias]
    issues: list[str] = []

    def _require_string(field: str):
        value = db_section.get(field)
        if value is None:
            issues.append(f"connections.{alias}.{field}: value is missing")
            return None
        if not isinstance(value, str):
            issues.append(f"connections.{alias}.{field}: value must be a string")
            return None
        return value

    file_host = db_section.get("host")
    if file_host is not None and not isinstance(file_host, str):
        issues.append(f"connections.{alias}.host: value must be a string")
        file_host = None

    env_host_key = f"DBBRO_DB_HOST_{alias.upper()}"
    host = file_host
    if not host:
        env_host = env.get(env_host_key, "")
        host = env_host if env_host else None

    if host is None:
        issues.append(
            f"connections.{alias}.host: no host available in the configuration "
            f"file or the {env_host_key} environment variable"
        )

    name = _require_string("name")
    user = _require_string("user")

    port = db_section.get("port")
    if port is not None and not isinstance(port, int):
        issues.append(f"connections.{alias}.port: value must be an integer")
        port = None

    file_password = db_section.get("password")
    if file_password is not None and not isinstance(file_password, str):
        issues.append(f"connections.{alias}.password: value must be a string")
        file_password = None

    env_pwd_key = f"DBBRO_DB_PWD_{alias.upper()}"
    password = file_password
    if not password:
        env_password = env.get(env_pwd_key, "")
        password = env_password if env_password else None

    if password is None:
        issues.append(
            f"connections.{alias}.password: no password available in the "
            f"configuration file or the {env_pwd_key} environment variable"
        )

    if issues:
        raise DatabaseConfigError(issues)

    return DatabaseConfig(host=host, name=name, user=user, password=password, port=port)
