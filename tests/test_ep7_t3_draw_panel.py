import curses

from dbbro.ui.screen import PANEL_CHARS, draw_panel
from tests.stub_screen import StubScreen


def test_draw_panel_writes_header_and_one_row_per_column():
    screen = StubScreen()
    rows = [("id", "1"), ("name", "Acme")]

    draw_panel(screen, "Company", rows, highlighted_index=0, scroll_offset=0)

    text = screen.all_text()
    assert "Company" in text
    assert "id" in text
    assert "1" in text
    assert "name" in text
    assert "Acme" in text


def test_draw_panel_draws_single_line_border_characters():
    screen = StubScreen()

    draw_panel(screen, "Company", [("id", "1")], highlighted_index=0, scroll_offset=0)

    text = screen.all_text()
    assert PANEL_CHARS["tl"] in text
    assert PANEL_CHARS["tr"] in text
    assert PANEL_CHARS["bl"] in text
    assert PANEL_CHARS["br"] in text
    assert PANEL_CHARS["v"] in text


def test_draw_panel_applies_reverse_video_only_to_highlighted_row():
    screen = StubScreen()
    rows = [("id", "1"), ("name", "Acme"), ("uuid", "abc")]

    draw_panel(screen, "Company", rows, highlighted_index=1, scroll_offset=0)

    reverse_calls = [c for c in screen.calls if isinstance(c, tuple) and c[3] & curses.A_REVERSE]
    assert len(reverse_calls) == 1
    assert "name" in reverse_calls[0][2]


def test_draw_panel_truncates_values_wider_than_terminal_width():
    screen = StubScreen(height=24, width=15)
    rows = [("name", "a very very very long value indeed")]

    draw_panel(screen, "Company", rows, highlighted_index=0, scroll_offset=0)

    for call in screen.calls:
        if isinstance(call, tuple):
            assert len(call[2]) <= screen._width


def test_draw_panel_shows_only_rows_within_scroll_window():
    # visible_height = (7-1) - 1 - 4 = 1: the bottom row is reserved for the
    # EP-2 help bar, and row 1 is where the panel (now flush against the
    # breadcrumb, with no separator row) starts.
    screen = StubScreen(height=7, width=80)
    rows = [("a", "1"), ("b", "2"), ("c", "3"), ("d", "4")]

    draw_panel(screen, "T", rows, highlighted_index=2, scroll_offset=2)

    text = screen.all_text()
    assert "c" in text
    assert "a" not in text
    assert "b" not in text
    assert "d" not in text


def test_draw_panel_pads_short_row_lists_with_blank_non_selectable_rows():
    screen = StubScreen(height=10, width=80)
    rows = [("a", "1")]

    draw_panel(screen, "T", rows, highlighted_index=0, scroll_offset=0)

    reverse_calls = [c for c in screen.calls if isinstance(c, tuple) and c[3] & curses.A_REVERSE]
    assert len(reverse_calls) == 1

    calls = [c for c in screen.calls if isinstance(c, tuple)]
    max_y = max(c[0] for c in calls)
    # The bottom border still reaches the row above the help bar, even
    # though there's only one real row of data.
    assert max_y == screen._height - 2
