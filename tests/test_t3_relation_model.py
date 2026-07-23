from dbbro.config.models import Relation


def test_relation_has_target_local_foreign():
    relation = Relation(
        target_table="Company",
        local_column="member_id",
        foreign_column="id",
    )

    assert relation.target_table == "Company"
    assert relation.local_column == "member_id"
    assert relation.foreign_column == "id"
