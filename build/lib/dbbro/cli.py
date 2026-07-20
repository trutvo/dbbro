import argparse
import curses
import os
import sys

from .config.errors import ConfigValidationError
from .config.loader import read_yaml_file
from .config.models import Config
from .config.validate import validate_config
from .db.connection import connect
from .db.database_config import resolve_database_config
from .db.errors import DatabaseConfigError, DatabaseConnectionError
from .ui import app as ui_app


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dbbro")
    parser.add_argument(
        "--config", required=True, help="Path to the YAML schema configuration file"
    )
    return parser


def run_ui(config: Config, conn) -> None:
    """Entry point into the application UI: enters the curses main loop,
    starting on the search selection dialog (NFR1)."""
    curses.wrapper(lambda stdscr: ui_app.run(stdscr, config, conn=conn))


def _report_and_exit(exc: Exception) -> int:
    for issue in getattr(exc, "issues", None) or [str(exc)]:
        print(str(issue), file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        raw = read_yaml_file(args.config)
        config = validate_config(raw)
    except ConfigValidationError as exc:
        return _report_and_exit(exc)

    try:
        db_config = resolve_database_config(raw, env=os.environ)
        conn = connect(db_config)
    except (DatabaseConfigError, DatabaseConnectionError) as exc:
        return _report_and_exit(exc)

    run_ui(config, conn)
    return 0


if __name__ == "__main__":
    sys.exit(main())
