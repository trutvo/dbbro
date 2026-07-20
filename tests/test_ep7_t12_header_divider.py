from dbbro.ui.screen import PANEL_CHARS, draw_panel
from tests.stub_screen import StubScreen


def _row_text(screen, y):
    return next(c[2] for c in screen.calls if isinstance(c, tuple) and c[0] == y)


def test_header_row_has_vertical_divider_matching_border_column_position():
    screen = StubScreen(width=200)
    rows = [("id", "1"), ("name", "Acme")]

    draw_panel(screen, "Company", rows, highlighted_index=0, scroll_offset=0)

    top_border = _row_text(screen, 0)
    header_row = _row_text(screen, 1)
    divider_row = _row_text(screen, 2)

    top_branch_col = top_border.index(PANEL_CHARS["t_down"])
    divider_branch_col = divider_row.index(PANEL_CHARS["cross"])
    header_bar_col = header_row.index(PANEL_CHARS["v"], 1)

    assert top_branch_col == divider_branch_col == header_bar_col


def test_header_row_shows_full_table_name_even_when_longer_than_column_names():
    screen = StubScreen(width=200)
    rows = [("id", "1"), ("x", "y")]

    draw_panel(screen, "VeryLongTableName", rows, highlighted_index=0, scroll_offset=0)

    header_row = _row_text(screen, 1)
    assert "VeryLongTableName" in header_row
