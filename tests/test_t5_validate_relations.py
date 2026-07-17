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
            "label": "belongs to ghost",
        }
    ]

    issues = validate_relations(raw)

    assert any(
        i.relation_label == "belongs to ghost" and "undeclared table" in i.message
        for i in issues
    )


def test_validate_rejects_relation_with_undeclared_local_or_foreign_column():
    raw = {"tables": _base_tables()}
    raw["tables"]["Membership"]["relations"] = [
        {
            "table": "Company",
            "local_column": "nope",
            "foreign_column": "nope_either",
            "label": "belongs to company",
        }
    ]

    issues = validate_relations(raw)

    messages = [i.message for i in issues if i.relation_label == "belongs to company"]
    assert any("local column" in m for m in messages)
    assert any("foreign column" in m for m in messages)


def test_validate_accepts_self_relation():
    raw = {"tables": _base_tables()}
    raw["tables"]["Membership"]["relations"] = [
        {
            "table": "Membership",
            "local_column": "member_id",
            "foreign_column": "id",
            "label": "refers to another membership",
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
            "label": "same as company",
        }
    ]

    issues = validate_relations(raw)

    assert issues == []


def test_validate_rejects_duplicate_relation_labels_across_tables():
    tables = _base_tables()
    tables["Company"]["relations"] = [
        {
            "table": "Membership",
            "local_column": "id",
            "foreign_column": "member_id",
            "label": "shared label",
        }
    ]
    tables["Membership"]["relations"] = [
        {
            "table": "Company",
            "local_column": "member_id",
            "foreign_column": "id",
            "label": "shared label",
        }
    ]
    raw = {"tables": tables}

    issues = validate_relations(raw)

    assert any(
        i.relation_label == "shared label" and "more than one relation" in i.message
        for i in issues
    )
