from dataclasses import dataclass

from . import keys
from .screen import draw_modal


@dataclass
class ErrorNotice:
    message: str

    def render(self, screen) -> None:
        draw_modal(screen, [self.message])

    def handle_key(self, key: int) -> bool:
        """Return True (dismissed) only when key is Return; otherwise ignore."""
        return key in keys.RETURN_ALTERNATES
