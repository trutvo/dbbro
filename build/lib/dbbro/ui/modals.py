from dataclasses import dataclass

from . import keys


@dataclass
class ErrorNotice:
    message: str

    def render(self, screen) -> None:
        pass

    def handle_key(self, key: int) -> bool:
        """Return True (dismissed) only when key is Return; otherwise ignore."""
        return key in keys.RETURN_ALTERNATES
