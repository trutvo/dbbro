from dataclasses import dataclass

SEPARATOR = " · "


@dataclass(frozen=True)
class HelpKey:
    """A single navigation key entry for the bottom help line.

    `priority` — lower number = higher priority = kept longest under
    truncation (0 = move/select, 1 = open/confirm, 2 = back/cancel,
    3 = quit/global, by convention; not enforced by types).
    """

    key_label: str
    action_label: str
    priority: int

    def render(self) -> str:
        return f"{self.key_label} {self.action_label}"


# Shared by every view whose Up/Down cycles the highlighted/selected row
# (TableView, SelectionList, SearchSelectionDialog), so the common shape
# isn't re-typed as literal HelpKey(...) construction in each module.
MOVE_KEY = HelpKey("↑/↓", "move", priority=0)
BACK_KEY = HelpKey("esc", "back", priority=2)


def _fits(keys: list[HelpKey], width: int) -> bool:
    return len(SEPARATOR.join(key.render() for key in keys)) <= width


def render_help_line(keys: list[HelpKey], width: int) -> str:
    """Joins `keys` (in their given order) with " · ", dropping the
    lowest-priority (highest `priority` value) entry and retrying until the
    result fits `width`. Returns "" if `keys` is empty or width <= 0 or even
    zero keys don't fit."""
    if width <= 0:
        return ""

    remaining = list(keys)
    while remaining and not _fits(remaining, width):
        drop_index = max(range(len(remaining)), key=lambda i: remaining[i].priority)
        remaining.pop(drop_index)

    if not remaining:
        return ""

    line = SEPARATOR.join(key.render() for key in remaining)
    return line if len(line) <= width else ""
