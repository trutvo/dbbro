from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HistoryEntry:
    """Wraps one visited table view. `view` is treated as opaque by History —
    in this codebase it is the already-built TableView instance (its fields
    are resolved once at construction time), so re-displaying an entry never
    repeats a search or relation lookup (NFR1)."""

    view: Any
