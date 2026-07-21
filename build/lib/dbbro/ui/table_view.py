from typing import Any

from ..config.models import Config, Table
from ..db.queries import fetch_by_column_equals
from ..navigation.breadcrumb import Breadcrumb, BreadcrumbStop
from . import keys
from .errors import RelationLookupFailedError
from .fields import RelationField, build_fields
from .screen import draw_panel
from .selection_list import SelectionList
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
        self.selected = 0
        self.scroll_offset = 0

    def render(self, screen) -> None:
        rows = [(field.column, field.value) for field in self.fields]
        draw_panel(
            screen,
            self.table.name,
            rows,
            highlighted_index=self.selected,
            scroll_offset=self.scroll_offset,
        )

    def handle_key(self, key: int) -> Transition | None:
        if key == keys.DOWN:
            self.selected = (self.selected + 1) % len(self.fields)
            self._update_scroll()
            return None
        if key == keys.UP:
            self.selected = (self.selected - 1) % len(self.fields)
            self._update_scroll()
            return None
        if key in keys.RETURN_ALTERNATES:
            return self._follow_selected_field()
        return None

    def _update_scroll(self) -> None:
        if self.selected < self.scroll_offset:
            self.scroll_offset = self.selected
        elif self.selected >= self.scroll_offset + self.visible_height:
            self.scroll_offset = self.selected - self.visible_height + 1

    def _follow_selected_field(self) -> Transition | None:
        field = self.fields[self.selected]
        if not isinstance(field, RelationField):
            return None

        target_table = self.config.tables[field.related_table]
        relation = next(
            r for r in self.table.relations if r.local_column == field.column
        )
        matches = fetch_by_column_equals(
            self.conn, target_table, relation.foreign_column, field.foreign_key_value
        )

        if not matches:
            raise RelationLookupFailedError()
        if len(matches) == 1:
            return Transition.push(self._build_table_view(target_table, matches[0]))
        return Transition.push(
            SelectionList(
                matches, lambda record: self._build_table_view(target_table, record)
            )
        )

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
