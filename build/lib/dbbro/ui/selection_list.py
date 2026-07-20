from typing import Any, Callable

from . import keys
from .view_stack import Transition


class SelectionList:
    """Modal list for picking one of several matching records.

    Used when a relation follow (or a search, per EP-2) matches more than
    one record: Up/Down highlights, Return confirms via `on_select`, which
    builds the view to push (the record's own table view).
    """

    def __init__(self, records: list[dict[str, Any]], on_select: Callable[[dict], Any]):
        self.records = records
        self.on_select = on_select
        self.highlighted = 0

    def render(self, screen) -> None:
        pass

    def handle_key(self, key: int) -> Transition | None:
        if key == keys.DOWN:
            self.highlighted = (self.highlighted + 1) % len(self.records)
            return None
        if key == keys.UP:
            self.highlighted = (self.highlighted - 1) % len(self.records)
            return None
        if key in keys.RETURN_ALTERNATES:
            record = self.records[self.highlighted]
            return Transition.push(self.on_select(record))
        if key == keys.ESCAPE:
            return Transition.pop()
        return None
