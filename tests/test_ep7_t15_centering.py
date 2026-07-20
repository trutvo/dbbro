from dbbro.ui.screen import draw_modal, draw_panel
from tests.stub_screen import StubScreen


def _bounds(screen):
    calls = [c for c in screen.calls if isinstance(c, tuple)]
    ys = [c[0] for c in calls]
    xs = [c[1] for c in calls]
    widths = [len(c[2]) for c in calls]
    return min(ys), max(ys), min(xs), max(x + w for x, w in zip(xs, widths))


def test_draw_modal_is_centered_horizontally_and_vertically():
    screen = StubScreen(height=40, width=100)

    draw_modal(screen, ["short line"])

    min_y, max_y, min_x, max_x = _bounds(screen)
    box_width = max_x - min_x
    box_height = max_y - min_y + 1
    assert min_x == (100 - box_width) // 2
    assert min_y == (40 - box_height) // 2


def test_draw_panel_is_centered_horizontally_and_vertically():
    screen = StubScreen(height=40, width=100)
    rows = [("id", "1"), ("name", "Acme")]

    draw_panel(screen, "Company", rows, highlighted_index=0, scroll_offset=0)

    min_y, max_y, min_x, max_x = _bounds(screen)
    box_width = max_x - min_x
    box_height = max_y - min_y + 1
    assert min_x == (100 - box_width) // 2
    assert min_y == (40 - box_height) // 2


def test_oversized_box_clamps_horizontally_instead_of_negative_position():
    screen = StubScreen(height=40, width=10)

    draw_modal(screen, ["this line is much too long for the terminal width"])

    xs = [c[1] for c in screen.calls if isinstance(c, tuple)]
    assert min(xs) == 0


def test_oversized_box_clamps_vertically_instead_of_negative_position():
    screen = StubScreen(height=3, width=100)

    draw_modal(screen, [f"line {i}" for i in range(20)])

    ys = [c[0] for c in screen.calls if isinstance(c, tuple)]
    assert min(ys) == 0
