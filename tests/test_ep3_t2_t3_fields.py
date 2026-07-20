from dbbro.config.models import Relation, Table
from dbbro.ui.fields import Field, RelationField, build_fields

PLAIN_TABLE = Table(name="Company", columns=("id", "name"), primary_key="id")

RELATION_TABLE = Table(
    name="Employee",
    columns=("id", "name", "company_id"),
    primary_key="id",
    relations=(
        Relation(
            target_table="Company",
            local_column="company_id",
            foreign_column="id",
            label="belongs to company",
        ),
    ),
)

TWO_RELATION_TABLE = Table(
    name="Employee",
    columns=("id", "name", "company_id", "manager_id"),
    primary_key="id",
    relations=(
        Relation(
            target_table="Company",
            local_column="company_id",
            foreign_column="id",
            label="belongs to company",
        ),
        Relation(
            target_table="Employee",
            local_column="manager_id",
            foreign_column="id",
            label="managed by",
        ),
    ),
)

PK_RELATION_TABLE = Table(
    name="Profile",
    columns=("user_id", "bio"),
    primary_key="user_id",
    relations=(
        Relation(
            target_table="User",
            local_column="user_id",
            foreign_column="id",
            label="profile of",
        ),
    ),
)


def test_build_fields_orders_fields_by_table_columns_order():
    row = {"id": "1", "name": "Acme"}

    fields = build_fields(PLAIN_TABLE, row)

    assert [f.column for f in fields] == ["id", "name"]


def test_build_fields_plain_column_shows_raw_value():
    row = {"id": "1", "name": "Acme"}

    fields = build_fields(PLAIN_TABLE, row)

    assert all(isinstance(f, Field) and not isinstance(f, RelationField) for f in fields)
    assert fields[1].value == "Acme"


def test_build_fields_relation_column_uses_related_table_bracket_fk_format():
    row = {"id": "1", "name": "Alice", "company_id": "42"}

    fields = build_fields(RELATION_TABLE, row)

    relation_field = fields[2]
    assert isinstance(relation_field, RelationField)
    assert relation_field.value == "Company[42]"


def test_build_fields_relation_column_includes_configured_label():
    row = {"id": "1", "name": "Alice", "company_id": "42"}

    fields = build_fields(RELATION_TABLE, row)

    assert fields[2].label == "belongs to company"


def test_build_fields_relation_on_primary_key_still_formatted_as_relation():
    row = {"user_id": "7", "bio": "hi"}

    fields = build_fields(PK_RELATION_TABLE, row)

    pk_field = fields[0]
    assert isinstance(pk_field, RelationField)
    assert pk_field.value == "User[7]"


def test_build_fields_two_relations_produce_two_independent_relation_fields():
    row = {"id": "1", "name": "Alice", "company_id": "42", "manager_id": "9"}

    fields = build_fields(TWO_RELATION_TABLE, row)

    relation_fields = [f for f in fields if isinstance(f, RelationField)]
    assert len(relation_fields) == 2
    assert relation_fields[0].value == "Company[42]"
    assert relation_fields[1].value == "Employee[9]"
