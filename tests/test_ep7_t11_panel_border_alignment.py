from dbbro.ui.screen import draw_panel
from tests.stub_screen import StubScreen


def test_all_drawn_lines_have_equal_length_regardless_of_field_value_lengths():
    screen = StubScreen(width=200)
    rows = [
        ("id", "1"),
        ("name", "Acme Corporation International Holdings"),
        ("uuid", "x"),
        ("member_id", "Membership[879874]"),
    ]

    draw_panel(screen, "Company", rows, highlighted_index=0, scroll_offset=0)

    lengths = {len(call[2]) for call in screen.calls if isinstance(call, tuple)}
    assert len(lengths) == 1, f"drawn lines have inconsistent widths: {lengths}"


def test_vertical_bars_align_in_the_same_column_across_all_rows():
    screen = StubScreen(width=200)
    rows = [("a", "1"), ("bb", "22"), ("ccc", "333")]

    draw_panel(screen, "T", rows, highlighted_index=0, scroll_offset=0)

    data_lines = [
        call[2] for call in screen.calls
        if isinstance(call, tuple) and 3 <= call[0] < 3 + len(rows)
    ]
    bar_positions = {line.find("│", 1) for line in data_lines}  # position of the divider bar
    assert len(bar_positions) == 1, f"divider bar column varies across rows: {bar_positions}"
