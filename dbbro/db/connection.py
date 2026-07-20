import pymysql

from .errors import DatabaseConnectionError
from .models import DatabaseConfig

DEFAULT_PORT = 3306


def connect(config: DatabaseConfig):
    """Opens a PyMySQL (MySQL) connection using config's resolved values.
    Raises DatabaseConnectionError (message naming host/database name only,
    never the password) if the connection cannot be established."""
    try:
        conn = pymysql.connect(
            host=config.host,
            port=config.port if config.port is not None else DEFAULT_PORT,
            db=config.name,
            user=config.user,
            password=config.password,
        )
    except pymysql.MySQLError as exc:
        raise DatabaseConnectionError(
            f"could not connect to database '{config.name}' at host "
            f"'{config.host}' (see chained exception for driver details)"
        ) from exc
    conn.cursorclass = pymysql.cursors.DictCursor
    return conn
