from dbbro.ui.help_bar import HelpKey
from dbbro.ui.screen import draw_help_bar, draw_modal, draw_panel
from tests.stub_screen import StubScreen
from dbbro.ui.relation_rows import DisplayRow


def test_writes_help_line_at_last_row():
    screen = StubScreen(height=24, width=80)
    keys = [HelpKey("↑/↓", "move", priority=0), HelpKey("q", "quit", priority=3)]

    draw_help_bar(screen, keys)

    calls = [c for c in screen.calls if isinstance(c, tuple)]
    assert any(c[0] == screen._height - 1 for c in calls)


def test_draw_panel_reserves_bottom_row():
    screen = StubScreen(height=8, width=80)  # visible_height = max(1, 8-1-4-2)=1
    rows = [DisplayRow("a", "1", "field"), DisplayRow("b", "2", "field"), DisplayRow("c", "3", "field")]

    draw_panel(screen, rows, highlighted_index=0, scroll_offset=0)

    calls = [c for c in screen.calls if isinstance(c, tuple)]
    max_row_written = max(c[0] for c in calls)
    assert max_row_written <= screen._height - 2


def test_draw_modal_reserves_bottom_row():
    screen = StubScreen(height=8, width=80)
    lines = [f"line {i}" for i in range(10)]

    draw_modal(screen, lines)

    calls = [c for c in screen.calls if isinstance(c, tuple)]
    max_row_written = max(c[0] for c in calls)
    assert max_row_written <= screen._height - 2
