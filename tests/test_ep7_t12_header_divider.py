from dbbro.ui.screen import draw_panel
from tests.stub_screen import StubScreen
from dbbro.ui.relation_rows import DisplayRow


def _row_text(screen, relative_row):
    """Returns the text of the `relative_row`-th drawn row, counting from
    whichever row the panel actually starts at (it may not be row 0)."""
    rows = sorted(c for c in screen.calls if isinstance(c, tuple))
    return rows[relative_row][2]


def test_header_row_and_body_rows_all_span_the_same_width():
    # There's no separate header line anymore: the first line drawn is
    # the section's own top border, and the body rows that follow must
    # span the same width as it.
    screen = StubScreen(width=200)
    rows = [DisplayRow("id", "1", "field"), DisplayRow("name", "Acme", "field")]

    draw_panel(screen, rows, highlighted_index=0, scroll_offset=0)

    top_border_row = _row_text(screen, 0)
    body_row = _row_text(screen, 1)

    assert len(top_border_row) == len(body_row) == screen._width


def test_body_rows_start_after_one_blank_margin_line_below_the_section_top_border():
    screen = StubScreen(width=200)
    rows = [DisplayRow("id", "1", "field"), DisplayRow("name", "Acme", "field")]

    draw_panel(screen, rows, highlighted_index=0, scroll_offset=0)

    all_rows = sorted(c for c in screen.calls if isinstance(c, tuple))
    # section top border, one blank top-margin line, one call per data row,
    # one blank bottom-margin line, section bottom border -- no header line
    # since there's only one section.
    assert len(all_rows) == 1 + 1 + len(rows) + 1 + 1
    ys = [c[0] for c in all_rows]
    assert ys == sorted(ys)
    # The panel's very first drawn line is the section's top border,
    # starting right at TOP_RESERVED_ROWS with nothing above it.
    assert all_rows[0][2].startswith("┌─")
    assert all_rows[-1][2].startswith("└─")


def test_section_top_border_shows_full_title_even_when_longer_than_column_names():
    # The box's title (e.g. the table name, baked into the leading
    # "section" row by build_display_rows) can be longer than any
    # column name without corrupting the box layout.
    screen = StubScreen(width=200)
    rows = [
        DisplayRow("", "  VeryLongTableName", "section"),
        DisplayRow("id", "1", "field"),
        DisplayRow("x", "y", "field"),
    ]

    draw_panel(screen, rows, highlighted_index=0, scroll_offset=0)

    top_border_row = _row_text(screen, 0)
    assert "VeryLongTableName" in top_border_row
    assert top_border_row.startswith("┌─")
    assert len(top_border_row) == screen._width
