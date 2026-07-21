from dbbro.navigation.breadcrumb import BreadcrumbStop
from dbbro.ui.screen import (
    TOP_RESERVED_ROWS,
    draw_breadcrumb_bar,
    draw_modal,
    draw_panel,
)
from tests.stub_screen import StubScreen


def test_writes_breadcrumb_line_at_row_zero():
    screen = StubScreen()

    draw_breadcrumb_bar(screen, [BreadcrumbStop(table="Shop", primary_key_value="543334")])

    rows = [c[0] for c in screen.calls if isinstance(c, tuple)]
    assert 0 in rows
    assert any(c[0] == 0 and "Shop" in c[2] for c in screen.calls if isinstance(c, tuple))


def test_draw_panel_reserves_top_two_rows():
    screen = StubScreen()

    draw_panel(screen, "Company", [("id", "1")], highlighted_index=0, scroll_offset=0)

    rows = [c[0] for c in screen.calls if isinstance(c, tuple)]
    assert all(r >= TOP_RESERVED_ROWS for r in rows)


def test_draw_modal_reserves_top_two_rows():
    screen = StubScreen()

    draw_modal(screen, ["line one"], highlighted_index=None)

    rows = [c[0] for c in screen.calls if isinstance(c, tuple)]
    assert all(r >= TOP_RESERVED_ROWS for r in rows)


def test_breadcrumb_bar_renders_without_crashing_on_small_terminal():
    screen = StubScreen(height=3, width=20)

    draw_breadcrumb_bar(screen, [])

    assert any(c[0] == 0 for c in screen.calls if isinstance(c, tuple))
