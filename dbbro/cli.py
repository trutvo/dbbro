import argparse
import sys

from .config.api import load_config
from .config.errors import ConfigValidationError
from .config.models import Config


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dbbro")
    parser.add_argument(
        "--config", required=True, help="Path to the YAML schema configuration file"
    )
    return parser


def run_ui(config: Config) -> None:
    """Entry point into the application UI, implemented by later epics."""
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigValidationError as exc:
        for issue in exc.issues:
            print(str(issue), file=sys.stderr)
        return 1

    run_ui(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
