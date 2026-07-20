from dbbro.ui.screen import truncate, update_scroll


def test_truncate_returns_text_unchanged_when_within_width():
    assert truncate("hello", 10) == "hello"


def test_truncate_cuts_text_to_width_when_too_long():
    assert truncate("hello world", 5) == "hello"


def test_update_scroll_moves_offset_up_when_selection_above_viewport():
    assert update_scroll(selected=2, offset=5, visible_height=10) == 2


def test_update_scroll_moves_offset_down_when_selection_below_viewport():
    assert update_scroll(selected=15, offset=0, visible_height=10) == 6


def test_update_scroll_leaves_offset_unchanged_when_selection_already_visible():
    assert update_scroll(selected=5, offset=3, visible_height=10) == 3
