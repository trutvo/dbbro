from dbbro.ui.search_prompt import FIELD_WIDTH, SearchValuePrompt
from tests.stub_screen import StubScreen


def _drawn_line(screen):
    lines = [c[2] for c in screen.calls if isinstance(c, tuple)]
    # the content row is the one containing the label/value text
    return next(line for line in lines if "Company.name" in line or line.strip("│ ") == "")


def test_field_width_is_128():
    assert FIELD_WIDTH == 128


def test_short_typed_value_is_padded_to_field_width():
    prompt = SearchValuePrompt("Company", "name")
    prompt.buffer = "Acme"
    screen = StubScreen(width=200)

    prompt.render(screen)

    line = _drawn_line(screen)
    content = line.strip("│").strip(" ")
    # content between the box borders (minus the 1-space padding each side)
    inner = line[2:-2]
    assert len(inner) == FIELD_WIDTH
    assert inner.startswith("Company.name: Acme")


def test_long_typed_value_is_truncated_on_screen_but_buffer_unaffected():
    long_value = "x" * 200
    prompt = SearchValuePrompt("Company", "name")
    prompt.buffer = long_value
    screen = StubScreen(width=200)

    prompt.render(screen)

    line = _drawn_line(screen)
    inner = line[2:-2]
    assert len(inner) == FIELD_WIDTH
    assert prompt.buffer == long_value  # underlying buffer is never truncated


def test_empty_buffer_still_produces_full_width_field():
    prompt = SearchValuePrompt("Company", "name")
    screen = StubScreen(width=200)

    prompt.render(screen)

    line = _drawn_line(screen)
    inner = line[2:-2]
    assert len(inner) == FIELD_WIDTH
