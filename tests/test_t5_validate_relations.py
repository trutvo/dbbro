from dbbro.config.validate import validate_relations


def _base_tables():
    return {
        "Company": {"columns": ["id", "name"], "primary_key": "id"},
        "Membership": {
            "columns": ["id", "member_id"],
            "primary_key": "id",
            "relations": [],
        },
    }


def test_validate_rejects_relation_to_undeclared_table():
    raw = {"tables": _base_tables()}
    raw["tables"]["Membership"]["relations"] = [
        {
            "table": "Ghost",
            "local_column": "member_id",
            "foreign_column": "id",
        }
    ]

    issues = validate_relations(raw)

    assert any(
        i.relation_label == "member_id -> Ghost" and "undeclared table" in i.message
        for i in issues
    )


def test_validate_rejects_relation_with_undeclared_local_or_foreign_column():
    raw = {"tables": _base_tables()}
    raw["tables"]["Membership"]["relations"] = [
        {
            "table": "Company",
            "local_column": "nope",
            "foreign_column": "nope_either",
        }
    ]

    issues = validate_relations(raw)

    messages = [i.message for i in issues if i.relation_label == "nope -> Company"]
    assert any("local column" in m for m in messages)
    assert any("foreign column" in m for m in messages)


def test_validate_accepts_self_relation():
    raw = {"tables": _base_tables()}
    raw["tables"]["Membership"]["relations"] = [
        {
            "table": "Membership",
            "local_column": "member_id",
            "foreign_column": "id",
        }
    ]

    issues = validate_relations(raw)

    assert issues == []


def test_validate_accepts_local_column_equal_to_primary_key():
    raw = {"tables": _base_tables()}
    raw["tables"]["Membership"]["relations"] = [
        {
            "table": "Company",
            "local_column": "id",
            "foreign_column": "id",
        }
    ]

    issues = validate_relations(raw)

    assert issues == []
