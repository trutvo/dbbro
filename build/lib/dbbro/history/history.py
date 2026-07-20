from typing import Any

from .models import HistoryEntry


class History:
    """Pure, callback-free stack-with-pointer of visited table views.

    Never imports or calls into ui/, EP-2, or EP-3 — callers push already-
    resolved views and receive already-resolved entries back.
    """

    def __init__(self) -> None:
        self._entries: list[HistoryEntry] = []
        self._position: int = -1

    def add_entry(self, view: Any) -> HistoryEntry:
        """Discard any entries after the current position (FR11/AC9), append
        a new entry, move the current position to it, and return it. Always
        adds a new entry, even for an exact revisit (FR10/AC10)."""
        entry = HistoryEntry(view=view)
        del self._entries[self._position + 1 :]
        self._entries.append(entry)
        self._position = len(self._entries) - 1
        return entry

    def go_back(self) -> HistoryEntry | None:
        """Move one entry earlier and return it. Returns None and leaves the
        position unchanged if already at the earliest entry (FR5/AC6)."""
        if self._position <= 0:
            return None
        self._position -= 1
        return self._entries[self._position]

    def go_forward(self) -> HistoryEntry | None:
        """Symmetric to go_back: moves one entry later, or returns None at
        the most recent entry (FR7/AC8)."""
        if self._position >= len(self._entries) - 1:
            return None
        self._position += 1
        return self._entries[self._position]

    def current(self) -> HistoryEntry | None:
        """The entry at the current position, or None if empty (FR9/AC11)."""
        if self._position < 0:
            return None
        return self._entries[self._position]
