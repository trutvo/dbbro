from typing import Any, Callable

from . import keys
from .screen import draw_modal, update_scroll
from .view_stack import Transition

DEFAULT_VISIBLE_HEIGHT = 20


class SelectionList:
    """Modal list for picking one of several matching records.

    Used when a relation follow (or a search, per EP-2) matches more than
    one record: Up/Down highlights, Return confirms via `on_select`, which
    builds the view to push (the record's own table view).
    """

    def __init__(
        self,
        records: list[dict[str, Any]],
        on_select: Callable[[dict], Any],
        visible_height: int = DEFAULT_VISIBLE_HEIGHT,
    ):
        self.records = records
        self.on_select = on_select
        self.highlighted = 0
        self.scroll_offset = 0
        self.visible_height = visible_height

    def render(self, screen) -> None:
        lines = [", ".join(f"{k}={v}" for k, v in record.items()) for record in self.records]
        visible_lines = lines[self.scroll_offset : self.scroll_offset + self.visible_height]
        draw_modal(
            screen,
            visible_lines,
            highlighted_index=self.highlighted - self.scroll_offset,
        )

    def _update_scroll(self) -> None:
        self.scroll_offset = update_scroll(
            self.highlighted, self.scroll_offset, self.visible_height
        )

    def handle_key(self, key: int) -> Transition | None:
        if key == keys.DOWN:
            self.highlighted = (self.highlighted + 1) % len(self.records)
            self._update_scroll()
            return None
        if key == keys.UP:
            self.highlighted = (self.highlighted - 1) % len(self.records)
            self._update_scroll()
            return None
        if key in keys.RETURN_ALTERNATES:
            record = self.records[self.highlighted]
            return Transition.push(self.on_select(record))
        if key == keys.ESCAPE:
            return Transition.pop()
        return None
