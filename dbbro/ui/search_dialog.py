from . import keys
from .help_bar import BACK_KEY, MOVE_KEY, HelpKey
from .screen import draw_modal, update_scroll
from .search_prompt import SearchValuePrompt
from .view_stack import Transition

DEFAULT_VISIBLE_HEIGHT = 20


class SearchSelectionDialog:
    def __init__(
        self,
        pairs: list[tuple[str, str]],
        conn=None,
        config=None,
        breadcrumb=None,
        history=None,
        visible_height: int = DEFAULT_VISIBLE_HEIGHT,
    ):
        self.pairs = pairs
        self.conn = conn
        self.config = config
        self.breadcrumb = breadcrumb
        self.history = history
        self.highlighted = 0
        self.scroll_offset = 0
        self.visible_height = visible_height

    def render(self, screen) -> None:
        lines = [f"{table}.{column}" for table, column in self.pairs]
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

    def help_keys(self) -> list[HelpKey]:
        return [MOVE_KEY, HelpKey("enter", "search", priority=1), BACK_KEY]

    def handle_key(self, key: int) -> Transition | None:
        if key == keys.DOWN:
            self.highlighted = (self.highlighted + 1) % len(self.pairs)
            self._update_scroll()
            return None
        if key == keys.UP:
            self.highlighted = (self.highlighted - 1) % len(self.pairs)
            self._update_scroll()
            return None
        if key in keys.RETURN_ALTERNATES:
            table, column = self.pairs[self.highlighted]
            return Transition.push(
                SearchValuePrompt(
                    table,
                    column,
                    conn=self.conn,
                    config=self.config,
                    breadcrumb=self.breadcrumb,
                    history=self.history,
                )
            )
        if key == keys.ESCAPE:
            return Transition.pop()
        return None
