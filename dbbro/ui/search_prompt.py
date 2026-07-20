from . import keys
from .screen import draw_modal
from .view_stack import Transition


class SearchValuePrompt:
    def __init__(
        self,
        table: str,
        column: str,
        conn=None,
        config=None,
        breadcrumb=None,
        history=None,
    ):
        self.table = table
        self.column = column
        self.conn = conn
        self.config = config
        self.breadcrumb = breadcrumb
        self.history = history
        self.buffer = ""
        self.cursor = 0

    def render(self, screen) -> None:
        draw_modal(screen, [f"{self.table}.{self.column}: {self.buffer}"])

    def consumes_navigation_keys(self) -> bool:
        """Always True: this view owns Left/Right as cursor movement within
        its typed buffer, so the main loop must not treat them as history
        navigation while this view is on top (FR14/AC13)."""
        return True

    def handle_key(self, key: int) -> Transition | None:
        if key == keys.ESCAPE:
            return Transition.pop()
        if key == keys.LEFT:
            self.cursor = max(0, self.cursor - 1)
            return None
        if key == keys.RIGHT:
            self.cursor = min(len(self.buffer), self.cursor + 1)
            return None
        if key in keys.BACKSPACE_ALTERNATES:
            if self.cursor > 0:
                self.buffer = self.buffer[: self.cursor - 1] + self.buffer[self.cursor :]
                self.cursor -= 1
            return None
        if key in keys.RETURN_ALTERNATES:
            if not self.buffer:
                return None
            return self._submit()
        if 32 <= key < 127:
            self.buffer = self.buffer[: self.cursor] + chr(key) + self.buffer[self.cursor :]
            self.cursor += 1
            return None
        return None

    def _submit(self) -> Transition:
        from ..search.lookup import find_matches

        table = self.config.tables[self.table]
        outcome = find_matches(self.conn, table, self.column, self.buffer)
        return Transition.push(
            _outcome_view(outcome, self.conn, self.config, self.breadcrumb, self.history)
        )


def _build_table_view(table_name, record, conn, config, breadcrumb, history):
    from ..navigation.breadcrumb import BreadcrumbStop
    from .table_view import TableView

    table = config.tables[table_name]
    if breadcrumb is not None:
        breadcrumb.reset()
        breadcrumb.push(
            BreadcrumbStop(
                table=table.name, primary_key_value=str(record[table.primary_key])
            )
        )
    view = TableView(table, record, conn, config, breadcrumb, history)
    if history is not None:
        history.add_entry(view)
    return view


def _outcome_view(outcome, conn, config, breadcrumb, history):
    from ..search.models import MultipleMatches, NoMatch, SingleMatch
    from .errors import SearchFailedError
    from .selection_list import SelectionList

    if isinstance(outcome, MultipleMatches):
        return SelectionList(
            outcome.records,
            lambda record: _build_table_view(
                outcome.table, record, conn, config, breadcrumb, history
            ),
        )
    if isinstance(outcome, SingleMatch):
        return _build_table_view(
            outcome.table, outcome.record, conn, config, breadcrumb, history
        )
    if isinstance(outcome, NoMatch):
        raise SearchFailedError()
    raise AssertionError(f"unhandled outcome: {outcome!r}")
