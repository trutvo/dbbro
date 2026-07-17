import pytest

from dbbro.config.api import load_config
from dbbro.config.errors import ConfigValidationError


def test_load_config_missing_file_raises_single_issue(tmp_path):
    missing_path = tmp_path / "does_not_exist.yaml"

    with pytest.raises(ConfigValidationError) as exc_info:
        load_config(str(missing_path))

    assert len(exc_info.value.issues) == 1


def test_load_config_malformed_yaml_raises_single_issue(tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("tables: [unclosed")

    with pytest.raises(ConfigValidationError) as exc_info:
        load_config(str(bad_file))

    assert len(exc_info.value.issues) == 1


def test_load_config_valid_minimal_file_returns_config(tmp_path):
    good_file = tmp_path / "good.yaml"
    good_file.write_text(
        """
tables:
  Company:
    columns: [id, name]
    primary_key: id
    search_columns: [name]
"""
    )

    config = load_config(str(good_file))

    assert "Company" in config.tables
    assert config.tables["Company"].primary_key == "id"
