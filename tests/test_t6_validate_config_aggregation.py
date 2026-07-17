import pytest

from dbbro.config.errors import ConfigValidationError
from dbbro.config.validate import validate_config


def test_validate_config_reports_all_violations_from_multiple_rules_in_one_exception():
    raw = {
        "tables": {
            "Company": {
                "columns": ["id", "name"],
                "primary_key": "id",
                "relations": [
                    {
                        "table": "Ghost",
                        "local_column": "id",
                        "foreign_column": "id",
                        "label": "bad relation",
                    }
                ],
            },
            "Empty": {"columns": [], "primary_key": "id"},
        }
    }

    with pytest.raises(ConfigValidationError) as exc_info:
        validate_config(raw)

    issues = exc_info.value.issues
    assert any("undeclared table" in i.message for i in issues)
    assert any(i.table == "Empty" and "no columns" in i.message for i in issues)
    assert len(issues) >= 2


def test_validate_config_returns_config_when_valid():
    raw = {
        "tables": {
            "Company": {"columns": ["id", "name"], "primary_key": "id"},
        }
    }

    config = validate_config(raw)

    assert "Company" in config.tables
