from dbbro.ui.screen import MODAL_CHARS, draw_modal
from tests.stub_screen import StubScreen


def test_draw_modal_writes_every_line():
    screen = StubScreen()

    draw_modal(screen, ["Company.name", "Company.uuid"])

    text = screen.all_text()
    assert "Company.name" in text
    assert "Company.uuid" in text


def test_draw_modal_draws_double_line_border_characters():
    screen = StubScreen()

    draw_modal(screen, ["one line"])

    text = screen.all_text()
    assert MODAL_CHARS["tl"] in text
    assert MODAL_CHARS["tr"] in text
    assert MODAL_CHARS["bl"] in text
    assert MODAL_CHARS["br"] in text
    assert MODAL_CHARS["v"] in text


def test_draw_modal_applies_reverse_video_only_to_highlighted_line():
    import curses

    screen = StubScreen()

    draw_modal(screen, ["a", "b", "c"], highlighted_index=1)

    reverse_calls = [c for c in screen.calls if isinstance(c, tuple) and c[3] & curses.A_REVERSE]
    assert len(reverse_calls) == 1
    assert "b" in reverse_calls[0][2]


def test_draw_modal_truncates_lines_wider_than_terminal_width():
    screen = StubScreen(height=24, width=10)

    draw_modal(screen, ["this line is way too long to fit"])

    for call in screen.calls:
        if isinstance(call, tuple):
            assert len(call[2]) <= screen._width
