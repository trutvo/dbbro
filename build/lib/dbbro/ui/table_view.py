from typing import Any

from ..config.models import Config, Table
from ..navigation.breadcrumb import Breadcrumb, BreadcrumbStop
from . import keys
from .fields import build_fields
from .help_bar import MOVE_KEY, HelpKey
from .relation_rows import LocalColumnTarget, RelatedEntityTarget, RowTarget, build_display_rows
from .screen import draw_panel
from .view_stack import Transition

DEFAULT_VISIBLE_HEIGHT = 20


class TableView:
    def __init__(
        self,
        table: Table,
        record: dict[str, Any],
        conn,
        config: Config,
        breadcrumb: Breadcrumb,
        history=None,
        visible_height: int = DEFAULT_VISIBLE_HEIGHT,
    ):
        self.table = table
        self.record = record
        self.conn = conn
        self.config = config
        self.breadcrumb = breadcrumb
        self.history = history
        self.visible_height = visible_height
        # Snapshot of the breadcrumb's full stop stack at the moment this
        # view was reached, so navigating history back/forward to this view
        # can restore the exact path it was shown with, not just its own
        # table/record (going back would otherwise lose earlier hops).
        self.breadcrumb_snapshot = tuple(breadcrumb.as_list()) if breadcrumb is not None else ()
        self.fields = build_fields(table, record)
        self.rows, self.row_targets = build_display_rows(
            self.fields, table, config, conn
        )
        self.selected = 0
        self.scroll_offset = 0

    def render(self, screen) -> None:
        draw_panel(
            screen,
            self.table.name,
            self.rows,
            highlighted_index=self.selected,
            scroll_offset=self.scroll_offset,
        )

    def help_keys(self) -> list[HelpKey]:
        """↑/↓ move is always available; "enter open" only appears when
        pressing Enter on the highlighted row would actually open something
        (N2/AC6/AC7)."""
        result = [MOVE_KEY]
        if self._is_openable(self.row_targets[self.selected]):
            result.append(HelpKey("enter", "open", priority=1))
        return result

    @staticmethod
    def _is_openable(target: RowTarget) -> bool:
        if isinstance(target, RelatedEntityTarget):
            return True
        if isinstance(target, LocalColumnTarget):
            return len(target.matches) == 1
        return False

    def handle_key(self, key: int) -> Transition | None:
        if key == keys.DOWN:
            self.selected = (self.selected + 1) % len(self.rows)
            self._update_scroll()
            return None
        if key == keys.UP:
            self.selected = (self.selected - 1) % len(self.rows)
            self._update_scroll()
            return None
        if key in keys.RETURN_ALTERNATES:
            return self._open_selected_row()
        return None

    def _update_scroll(self) -> None:
        if self.selected < self.scroll_offset:
            self.scroll_offset = self.selected
        elif self.selected >= self.scroll_offset + self.visible_height:
            self.scroll_offset = self.selected - self.visible_height + 1

    def _open_selected_row(self) -> Transition | None:
        target = self.row_targets[self.selected]
        if isinstance(target, RelatedEntityTarget):
            table = self.config.tables[target.target_table]
            return Transition.push(self._build_table_view(table, target.record))
        if isinstance(target, LocalColumnTarget) and len(target.matches) == 1:
            table = self.config.tables[target.target_table]
            return Transition.push(self._build_table_view(table, target.matches[0]))
        return None

    def _build_table_view(self, table: Table, record: dict[str, Any]) -> "TableView":
        self.breadcrumb.push(
            BreadcrumbStop(
                table=table.name,
                primary_key_value=str(record[table.primary_key]),
            )
        )
        view = TableView(
            table,
            record,
            self.conn,
            self.config,
            self.breadcrumb,
            self.history,
            visible_height=self.visible_height,
        )
        if self.history is not None:
            self.history.add_entry(view)
        return view
