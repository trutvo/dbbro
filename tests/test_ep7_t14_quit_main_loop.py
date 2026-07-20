from types import MappingProxyType

from dbbro.config.models import Config
from dbbro.ui import app as ui_app
from dbbro.ui import keys
from tests.stub_screen import StubScreen


class _StopLoop(Exception):
    pass


class _ScriptedScreen(StubScreen):
    def __init__(self, key_sequence):
        super().__init__()
        self._gets = iter(key_sequence)

    def getch(self):
        try:
            return next(self._gets)
        except StopIteration:
            raise _StopLoop


def test_q_then_return_quits_the_main_loop():
    config = Config(tables=MappingProxyType({}))
    screen = _ScriptedScreen([keys.Q, keys.RETURN_ALTERNATES[0]])

    # run() should return normally (not raise _StopLoop), since Return
    # inside the QuitConfirmation modal ends the loop via `return`.
    ui_app.run(screen, config, conn=None)


def test_q_then_escape_cancels_and_resumes_the_loop():
    import pytest

    config = Config(tables=MappingProxyType({}))
    # q opens the confirmation, Escape cancels it, then the loop continues
    # and the third scripted key runs out, raising _StopLoop as expected.
    screen = _ScriptedScreen([keys.Q, keys.ESCAPE])

    with pytest.raises(_StopLoop):
        ui_app.run(screen, config, conn=None)
