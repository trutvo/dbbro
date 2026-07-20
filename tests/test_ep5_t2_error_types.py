from dbbro.ui.errors import (
    OperationFailedError,
    RelationLookupFailedError,
    SearchFailedError,
)


def test_search_failed_error_message_identifies_search():
    assert "search" in str(SearchFailedError()).lower()


def test_relation_lookup_failed_error_message_identifies_relation_lookup():
    assert "relation" in str(RelationLookupFailedError()).lower()


def test_error_messages_are_distinct_between_the_two_types():
    assert str(SearchFailedError()) != str(RelationLookupFailedError())


def test_both_error_types_are_operation_failed_errors():
    assert issubclass(SearchFailedError, OperationFailedError)
    assert issubclass(RelationLookupFailedError, OperationFailedError)
