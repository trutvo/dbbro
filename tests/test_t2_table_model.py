from dbbro.config.models import Table


def test_table_with_no_search_columns_is_valid():
    table = Table(name="Membership", columns=("id", "member_id"), primary_key="id")

    assert table.search_columns == ()


def test_table_shape_fields_present():
    table = Table(
        name="Company",
        columns=("id", "name"),
        primary_key="id",
        search_columns=("name",),
    )

    assert table.name == "Company"
    assert table.columns == ("id", "name")
    assert table.primary_key == "id"
    assert table.search_columns == ("name",)
    assert table.relations == ()
