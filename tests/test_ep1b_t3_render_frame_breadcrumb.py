from dbbro.navigation.breadcrumb import Breadcrumb, BreadcrumbStop
from dbbro.ui.app import render_frame
from dbbro.ui.view_stack import ViewStack
from tests.stub_screen import StubScreen


class _FakeView:
    def render(self, screen) -> None:
        pass


class _FakeModal:
    def render(self, screen) -> None:
        pass


def test_breadcrumb_shows_root_label_before_any_search():
    screen = StubScreen()
    stack = ViewStack(_FakeView())
    breadcrumb = Breadcrumb()

    render_frame(screen, stack, None, breadcrumb)

    assert any(c[0] == 0 and "Tables" in c[2] for c in screen.calls if isinstance(c, tuple))


def test_breadcrumb_updates_after_drilling_into_relation():
    screen = StubScreen()
    stack = ViewStack(_FakeView())
    breadcrumb = Breadcrumb()
    breadcrumb.push(BreadcrumbStop(table="Shop", primary_key_value="543334"))

    render_frame(screen, stack, None, breadcrumb)

    assert any(c[0] == 0 and "Shop" in c[2] and "543334" in c[2] for c in screen.calls if isinstance(c, tuple))


def test_breadcrumb_visible_during_pending_error_modal():
    screen = StubScreen()
    stack = ViewStack(_FakeView())
    breadcrumb = Breadcrumb()
    breadcrumb.push(BreadcrumbStop(table="Shop", primary_key_value="543334"))

    render_frame(screen, stack, _FakeModal(), breadcrumb)

    assert any(c[0] == 0 and "Shop" in c[2] for c in screen.calls if isinstance(c, tuple))


def test_breadcrumb_visible_during_quit_confirmation():
    screen = StubScreen()
    stack = ViewStack(_FakeView())
    breadcrumb = Breadcrumb()
    breadcrumb.push(BreadcrumbStop(table="Shop", primary_key_value="543334"))

    render_frame(screen, stack, _FakeModal(), breadcrumb)

    assert any(c[0] == 0 and "Shop" in c[2] for c in screen.calls if isinstance(c, tuple))


def test_breadcrumb_reflects_new_search_after_reset():
    screen = StubScreen()
    stack = ViewStack(_FakeView())
    breadcrumb = Breadcrumb()
    breadcrumb.push(BreadcrumbStop(table="Shop", primary_key_value="543334"))
    breadcrumb.reset()
    breadcrumb.push(BreadcrumbStop(table="Employee", primary_key_value="9"))

    render_frame(screen, stack, None, breadcrumb)

    calls = [c for c in screen.calls if isinstance(c, tuple) and c[0] == 0]
    assert any("Employee" in c[2] and "9" in c[2] for c in calls)
    assert not any("Shop" in c[2] for c in calls)
