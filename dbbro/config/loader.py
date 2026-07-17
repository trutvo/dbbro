from pathlib import Path

import yaml

from .errors import ConfigIssue, ConfigValidationError


def read_yaml_file(path: str) -> dict:
    file_path = Path(path)
    if not file_path.is_file():
        raise ConfigValidationError(
            [ConfigIssue(message=f"configuration file not found: {path}")]
        )
    try:
        with file_path.open("r") as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigValidationError(
            [ConfigIssue(message=f"malformed YAML in {path}: {exc}")]
        ) from exc
    return content or {}
