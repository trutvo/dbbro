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
from .search.lookup import find_matches
from .search.models import NoMatch
from .ui import app as ui_app


class QuickSearchError(Exception):
    pass


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dbbro")
    parser.add_argument(
        "--config", required=True, help="Path to the YAML schema configuration file"
    )
    parser.add_argument(
        "--search",
        help=(
            "Quick-start search: '<Table>.<column>=<value>', e.g. "
            "'Company.uuid=72345024027900a9f5538097e82d7ceb'. <Table>.<column> "
            "must be one of the config's declared searchable columns."
        ),
    )
    return parser


def parse_quick_search(spec: str) -> tuple[str, str, str]:
    """Parses '<Table>.<column>=<value>'. Raises QuickSearchError on any
    malformed syntax (missing '=', missing '.', or an empty table, column,
    or value)."""
    if "=" not in spec:
        raise QuickSearchError(
            f"--search: missing '=' in {spec!r}; expected '<Table>.<column>=<value>'"
        )
    left, _, value = spec.partition("=")
    if "." not in left:
        raise QuickSearchError(
            f"--search: missing '.' in {left!r}; expected '<Table>.<column>=<value>'"
        )
    table_name, _, column = left.partition(".")
    if not table_name or not column:
        raise QuickSearchError(
            f"--search: table and column must both be non-empty in {spec!r}"
        )
    if not value:
        raise QuickSearchError(f"--search: search value must not be empty in {spec!r}")
    return table_name, column, value


def resolve_quick_search(spec: str, config: Config, conn):
    """Parses and validates a --search spec against the config's declared
    searchable columns, then runs the lookup. Raises QuickSearchError on
    malformed syntax, an unknown/non-searchable <Table>.<column>, or a
    zero-match result — every case that must exit before any UI opens."""
    table_name, column, value = parse_quick_search(spec)
    if (table_name, column) not in config.searchable_pairs():
        raise QuickSearchError(
            f"--search: '{table_name}.{column}' is not a declared searchable column"
        )
    outcome = find_matches(conn, config.tables[table_name], column, value)
    if isinstance(outcome, NoMatch):
        raise QuickSearchError(
            f"--search: no record found for {table_name}.{column}={value!r}"
        )
    return outcome


def run_ui(config: Config, conn, initial_outcome=None) -> None:
    """Entry point into the application UI: enters the curses main loop,
    starting on the search selection dialog (NFR1), or directly on
    `initial_outcome`'s result if a --search quick-start was given."""
    curses.wrapper(
        lambda stdscr: ui_app.run(
            stdscr, config, conn=conn, initial_outcome=initial_outcome
        )
    )


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

    initial_outcome = None
    if args.search:
        try:
            initial_outcome = resolve_quick_search(args.search, config, conn)
        except QuickSearchError as exc:
            return _report_and_exit(exc)

    run_ui(config, conn, initial_outcome=initial_outcome)
    return 0


if __name__ == "__main__":
    sys.exit(main())
