from dataclasses import dataclass

from . import keys
from .help_bar import HelpKey
from .screen import draw_modal


@dataclass
class ErrorNotice:
    message: str

    def render(self, screen) -> None:
        draw_modal(screen, [self.message])

    def help_keys(self) -> list[HelpKey]:
        return [HelpKey("enter", "dismiss", priority=1)]

    def handle_key(self, key: int) -> bool:
        """Return True (dismissed) only when key is Return; otherwise ignore."""
        return key in keys.RETURN_ALTERNATES


@dataclass
class QuitConfirmation:
    """Modal asking whether to quit dbbro. Return confirms, Escape cancels;
    every other key is ignored."""

    message: str = "Quit dbbro?"

    def render(self, screen) -> None:
        draw_modal(screen, [self.message])

    def help_keys(self) -> list[HelpKey]:
        return [HelpKey("enter", "quit", priority=1), HelpKey("esc", "cancel", priority=2)]

    def handle_key(self, key: int) -> str | None:
        """Returns 'confirm', 'cancel', or None (still open, key ignored)."""
        if key in keys.RETURN_ALTERNATES:
            return "confirm"
        if key == keys.ESCAPE:
            return "cancel"
        return None
