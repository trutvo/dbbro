from dbbro.ui.help_bar import HelpKey, render_help_line


def test_joins_keys_with_separator():
    keys = [
        HelpKey("↑/↓", "move", priority=0),
        HelpKey("enter", "open", priority=1),
        HelpKey("q", "quit", priority=3),
    ]

    result = render_help_line(keys, width=80)

    assert result == "↑/↓ move · enter open · q quit"


def test_drops_lowest_priority_first_when_overflowing():
    keys = [
        HelpKey("↑/↓", "move", priority=0),
        HelpKey("enter", "open", priority=1),
        HelpKey("q", "quit", priority=3),
    ]
    full = "↑/↓ move · enter open · q quit"
    width = len(full) - 1

    result = render_help_line(keys, width=width)

    assert "quit" not in result
    assert result == "↑/↓ move · enter open"


def test_never_exceeds_given_width():
    keys = [
        HelpKey("↑/↓", "move", priority=0),
        HelpKey("enter", "open", priority=1),
        HelpKey("esc", "back", priority=2),
        HelpKey("q", "quit", priority=3),
    ]

    for width in range(0, 41):
        result = render_help_line(keys, width=width)
        assert len(result) <= width


def test_empty_keys_returns_empty_string():
    assert render_help_line([], width=80) == ""
