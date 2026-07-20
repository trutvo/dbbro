from dbbro.ui.app import render_frame
from dbbro.ui.view_stack import ViewStack
from tests.stub_screen import StubScreen


class _StubView:
    def render(self, screen):
        screen.addstr(0, 0, "view content")

    def handle_key(self, key):
        return None


def test_main_loop_erases_screen_before_each_render():
    stack = ViewStack(_StubView())
    screen = StubScreen()

    render_frame(screen, stack, pending_modal=None)

    assert screen.calls[0] == "erase"


def test_render_frame_renders_pending_modal_after_current_view():
    class _StubModal:
        def render(self, screen):
            screen.addstr(1, 0, "modal content")

    stack = ViewStack(_StubView())
    screen = StubScreen()

    render_frame(screen, stack, pending_modal=_StubModal())

    text = screen.all_text()
    assert "view content" in text
    assert "modal content" in text
