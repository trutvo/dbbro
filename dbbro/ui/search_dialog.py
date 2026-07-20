from . import keys
from .search_prompt import SearchValuePrompt
from .view_stack import Transition


class SearchSelectionDialog:
    def __init__(
        self,
        pairs: list[tuple[str, str]],
        conn=None,
        config=None,
        breadcrumb=None,
        history=None,
    ):
        self.pairs = pairs
        self.conn = conn
        self.config = config
        self.breadcrumb = breadcrumb
        self.history = history
        self.highlighted = 0

    def render(self, screen) -> None:
        pass

    def handle_key(self, key: int) -> Transition | None:
        if key == keys.DOWN:
            self.highlighted = (self.highlighted + 1) % len(self.pairs)
            return None
        if key == keys.UP:
            self.highlighted = (self.highlighted - 1) % len(self.pairs)
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
