class OperationFailedError(Exception):
    """Base for a failed search or relation lookup; caught centrally by the main loop."""


class SearchFailedError(OperationFailedError):
    def __str__(self) -> str:
        return "Search failed: no matching record was found."


class RelationLookupFailedError(OperationFailedError):
    def __str__(self) -> str:
        return "Could not follow relation: the related record could not be looked up."
