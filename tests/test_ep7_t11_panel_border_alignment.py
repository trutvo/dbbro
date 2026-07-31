from dbbro.ui.screen import draw_panel
from tests.stub_screen import StubScreen
from dbbro.ui.relation_rows import DisplayRow


def test_all_drawn_lines_have_equal_length_regardless_of_field_value_lengths():
    screen = StubScreen(width=200)
    rows = [
        DisplayRow("id", "1", "field"),
        DisplayRow("name", "Acme Corporation International Holdings", "field"),
        DisplayRow("uuid", "x", "field"),
        DisplayRow("member_id", "Membership[879874]", "field"),
    ]

    draw_panel(screen, rows, highlighted_index=0, scroll_offset=0)

    lengths = {len(call[2]) for call in screen.calls if isinstance(call, tuple)}
    assert len(lengths) == 1, f"drawn lines have inconsistent widths: {lengths}"


def test_value_column_starts_in_the_same_position_across_all_rows():
    screen = StubScreen(width=200)
    rows = [DisplayRow("a", "1", "field"), DisplayRow("bb", "22", "field"), DisplayRow("ccc", "333", "field")]

    draw_panel(screen, rows, highlighted_index=0, scroll_offset=0)

    # Data rows are whichever rows were drawn 2nd through (2+len(rows))th,
    # counting from wherever the panel actually starts (there's the
    # section's top border, with no header line above it, before the data
    # rows begin).
    all_rows = sorted(call for call in screen.calls if isinstance(call, tuple))
    data_lines = [call[2] for call in all_rows[1 : 1 + len(rows)]]
    name_width = max(len(r.name) for r in rows)
    value_start = name_width + 2  # name column width plus the two-space gap
    for row, line in zip(rows, data_lines):
        interior = line[2:-2]  # strip the "| " / " |" box border padding
        assert interior[:value_start] == row.name.ljust(name_width) + "  "
