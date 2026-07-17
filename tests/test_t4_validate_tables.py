from dbbro.config.validate import validate_tables


def test_validate_rejects_primary_key_not_in_columns():
    raw = {
        "tables": {
            "Company": {"columns": ["id", "name"], "primary_key": "uuid"},
        }
    }

    issues = validate_tables(raw)

    assert any(i.table == "Company" and "primary key" in i.message for i in issues)


def test_validate_rejects_search_column_not_in_columns():
    raw = {
        "tables": {
            "Company": {
                "columns": ["id", "name"],
                "primary_key": "id",
                "search_columns": ["missing"],
            },
        }
    }

    issues = validate_tables(raw)

    assert any(
        i.table == "Company" and i.column == "missing" and "search column" in i.message
        for i in issues
    )


def test_validate_rejects_empty_column_list():
    raw = {"tables": {"Empty": {"columns": [], "primary_key": "id"}}}

    issues = validate_tables(raw)

    assert any(i.table == "Empty" and "no columns" in i.message for i in issues)


def test_validate_rejects_duplicate_column_names_in_table():
    raw = {
        "tables": {
            "Company": {"columns": ["id", "name", "name"], "primary_key": "id"},
        }
    }

    issues = validate_tables(raw)

    assert any(
        i.table == "Company" and i.column == "name" and "duplicate column" in i.message
        for i in issues
    )
