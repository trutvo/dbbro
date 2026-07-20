from .loader import read_yaml_file
from .models import Config
from .validate import validate_config


def load_config(path: str) -> Config:
    """Read, parse, and validate the YAML config at `path`.

    Raises ConfigValidationError (single exception, .issues holds every
    violation found) if the file is missing, unreadable, malformed YAML,
    or fails any structural/cross-referential rule.
    """
    raw = read_yaml_file(path)
    return validate_config(raw)
