import curses

from dbbro.ui.screen import draw_panel, TOP_RESERVED_ROWS
from tests.stub_screen import StubScreen
from dbbro.ui.relation_rows import DisplayRow


def test_draw_panel_writes_header_and_one_row_per_column():
    screen = StubScreen()
    rows = [
        DisplayRow("", "  Company", "section"),
        DisplayRow("id", "1", "field"),
        DisplayRow("name", "Acme", "field"),
    ]

    draw_panel(screen, rows, highlighted_index=0, scroll_offset=0)

    text = screen.all_text()
    assert "Company" in text
    assert "id" in text
    assert "1" in text
    assert "name" in text
    assert "Acme" in text


def test_draw_panel_draws_a_box_around_each_section():
    # Sections (split by "section"-kind rows) each render as their own
    # box, with the section's title embedded in the top border, a bottom
    # border, and body rows wrapped in "| ... |".
    screen = StubScreen()

    draw_panel(screen, [DisplayRow("id", "1", "field")], highlighted_index=0, scroll_offset=0)

    lines = [call[2] for call in screen.calls if isinstance(call, tuple)]
    top_borders = [line for line in lines if line.startswith("┌─")]
    bottom_borders = [line for line in lines if line.startswith("└─")]
    body_lines = [line for line in lines if line.startswith("│ ") and line.rstrip().endswith("│")]

    assert len(top_borders) == 1
    assert len(bottom_borders) == 1
    assert any("id" in line and "1" in line for line in body_lines)


def test_draw_panel_writes_section_title_in_bold_on_the_top_border():
    # There is no longer a standalone header line above the boxes; the
    # section's title is embedded directly in its box's top border, and
    # that border line is drawn bold.
    screen = StubScreen()

    draw_panel(
        screen,
        [DisplayRow("", "  Company", "section"), DisplayRow("id", "1", "field")],
        highlighted_index=1,
        scroll_offset=0,
    )

    calls = [c for c in screen.calls if isinstance(c, tuple)]
    title_calls = [c for c in calls if "Company" in c[2]]
    assert len(title_calls) == 1
    title_call = title_calls[0]
    assert title_call[3] & curses.A_BOLD
    assert not (title_call[3] & curses.A_REVERSE)


def test_draw_panel_applies_reverse_video_only_to_highlighted_row():
    screen = StubScreen()
    rows = [DisplayRow("id", "1", "field"), DisplayRow("name", "Acme", "field"), DisplayRow("uuid", "abc", "field")]

    draw_panel(screen, rows, highlighted_index=1, scroll_offset=0)

    reverse_calls = [c for c in screen.calls if isinstance(c, tuple) and c[3] & curses.A_REVERSE]
    assert len(reverse_calls) == 1
    assert "name" in reverse_calls[0][2]


def test_draw_panel_truncates_values_wider_than_terminal_width():
    screen = StubScreen(height=24, width=15)
    rows = [DisplayRow("name", "a very very very long value indeed", "field")]

    draw_panel(screen, rows, highlighted_index=0, scroll_offset=0)

    for call in screen.calls:
        if isinstance(call, tuple):
            assert len(call[2]) <= screen._width


def test_draw_panel_shows_only_rows_within_scroll_window():
    # usable_height = 4 - 1 = 3; start_y = TOP_RESERVED_ROWS (2); boxes
    # start right at TOP_RESERVED_ROWS with no header line above them, so
    # with visible_height = 3 - 2 = 1 and scroll_offset=2 only rows[2:3]
    # ("c") lands in the single visible data-row slot before the help bar
    # row is reached.
    screen = StubScreen(height=4, width=80)
    rows = [DisplayRow("a", "1", "field"), DisplayRow("b", "2", "field"), DisplayRow("c", "3", "field"), DisplayRow("d", "4", "field")]

    draw_panel(screen, rows, highlighted_index=2, scroll_offset=2)

    text = screen.all_text()
    assert "c" in text
    assert "a" not in text
    assert "b" not in text
    assert "d" not in text


def test_draw_panel_does_not_pad_short_row_lists_with_blank_rows():
    screen = StubScreen(height=10, width=80)
    rows = [DisplayRow("a", "1", "field")]

    draw_panel(screen, rows, highlighted_index=0, scroll_offset=0)

    reverse_calls = [c for c in screen.calls if isinstance(c, tuple) and c[3] & curses.A_REVERSE]
    assert len(reverse_calls) == 1

    # Only the row's box (top border + top margin + body + bottom margin +
    # bottom border) is drawn; nothing fills the remaining unused space down
    # to the help bar, and there is no separate header line above it.
    calls = [c for c in screen.calls if isinstance(c, tuple)]
    assert len(calls) == 5  # top border + top margin + one data row + bottom margin + bottom border
    max_y = max(c[0] for c in calls)
    assert max_y == TOP_RESERVED_ROWS + 4  # top border + top margin + data row + bottom margin + bottom border
