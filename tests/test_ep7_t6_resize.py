import curses

import pytest

from dbbro import cli
from dbbro.ui import app as ui_app
from dbbro.config.models import Config
from types import MappingProxyType
from tests.stub_screen import StubScreen


class _StopLoop(Exception):
    pass


class _ResizeThenStopScreen(StubScreen):
    def __init__(self):
        super().__init__()
        self._gets = iter([curses.KEY_RESIZE])

    def getch(self):
        try:
            return next(self._gets)
        except StopIteration:
            raise _StopLoop


def test_main_loop_calls_update_lines_cols_and_rerenders_on_key_resize(monkeypatch):
    calls = []
    monkeypatch.setattr(curses, "update_lines_cols", lambda: calls.append("update_lines_cols"))

    config = Config(tables=MappingProxyType({}))
    screen = _ResizeThenStopScreen()

    with pytest.raises(_StopLoop):
        ui_app.run(screen, config, conn=None)

    assert calls == ["update_lines_cols"]
