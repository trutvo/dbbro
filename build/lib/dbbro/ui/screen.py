import curses

PANEL_CHARS = {
    "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
    "h": "─", "v": "│", "cross": "┼", "t_down": "┬", "t_up": "┴",
    "t_right": "├", "t_left": "┤",
}
MODAL_CHARS = {
    "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
    "h": "═", "v": "║", "cross": "╬", "t_down": "╦", "t_up": "╩",
    "t_right": "╠", "t_left": "╣",
}


def truncate(text: str, width: int) -> str:
    """Returns text unchanged if it fits within width, else cuts it to width."""
    if width <= 0:
        return ""
    return text if len(text) <= width else text[:width]


def update_scroll(selected: int, offset: int, visible_height: int) -> int:
    """Clamp-to-viewport logic: returns a new offset such that `selected`
    stays within [offset, offset + visible_height)."""
    if selected < offset:
        return selected
    if selected >= offset + visible_height:
        return selected - visible_height + 1
    return offset


def _write_line(screen, y: int, x: int, text: str, attr: int = 0) -> None:
    screen.addstr(y, x, text, attr)


def _center_origin(box_width: int, box_height: int, max_width: int, max_height: int) -> tuple[int, int]:
    """Returns (start_y, start_x) so a box_width x box_height box is centered
    in the terminal, clamped to (0, 0) if it wouldn't otherwise fit."""
    start_y = max(0, (max_height - box_height) // 2)
    start_x = max(0, (max_width - box_width) // 2)
    return start_y, start_x


def draw_modal(screen, lines: list[str], highlighted_index: int | None = None) -> None:
    """Draws a double-line modal box around `lines`, sized to the longest
    line (truncated to the terminal's current width), centered in the
    terminal, reverse-videoing the line at `highlighted_index` if given."""
    max_height, max_width = screen.getmaxyx()
    inner_width = max(1, min((max((len(line) for line in lines), default=0)), max_width - 4))
    box_width = inner_width + 4
    box_height = len(lines) + 2
    start_y, start_x = _center_origin(box_width, box_height, max_width, max_height)

    c = MODAL_CHARS
    _write_line(screen, start_y, start_x, c["tl"] + c["h"] * (box_width - 2) + c["tr"])
    for i, line in enumerate(lines):
        content = truncate(line, inner_width)
        attr = curses.A_REVERSE if highlighted_index == i else 0
        row = start_y + 1 + i
        if row >= max_height - 1:
            break
        _write_line(screen, row, start_x, c["v"] + " " + content.ljust(inner_width) + " " + c["v"], attr)
    last_row = min(start_y + box_height - 1, max_height - 1)
    _write_line(screen, last_row, start_x, c["bl"] + c["h"] * (box_width - 2) + c["br"])


def draw_panel(
    screen,
    header: str,
    rows: list[tuple[str, str]],
    highlighted_index: int,
    scroll_offset: int,
) -> None:
    """Draws a single-line-bordered panel: `header` as the title row, then
    rows[scroll_offset:scroll_offset+visible_height] as name/value rows,
    truncating any value that doesn't fit and reverse-videoing the row at
    `highlighted_index`."""
    max_height, max_width = screen.getmaxyx()
    # The name column must fit the header text too, not just column names,
    # so a table name longer than every column name is never truncated
    # just because the divider now splits the header row (see draw_panel's
    # header-row construction below).
    name_width = max(len(header), max((len(name) for name, _ in rows), default=0))
    value_width = max((len(value) for _, value in rows), default=0)

    # Full border width = name_width + value_width + 7 (2 corners + 2 border
    # cells around each column + 1 divider). Shrink value_width first, then
    # name_width, to fit within the terminal (FR15).
    border_width = name_width + value_width + 7
    if border_width > max_width:
        excess = border_width - max_width
        shrink_value = min(value_width, excess)
        value_width -= shrink_value
        excess -= shrink_value
        if excess > 0:
            name_width = max(0, name_width - excess)
    value_width = max(1, value_width)
    box_width = name_width + value_width + 7

    visible_height = max(1, max_height - 4)
    visible_rows = rows[scroll_offset : scroll_offset + visible_height]
    box_height = 3 + len(visible_rows) + 1
    start_y, start_x = _center_origin(box_width, box_height, max_width, max_height)

    c = PANEL_CHARS
    _write_line(screen, start_y, start_x, c["tl"] + c["h"] * (name_width + 2) + c["t_down"] + c["h"] * (value_width + 2) + c["tr"])
    header_text = truncate(header, name_width).ljust(name_width)
    empty_cell = " " * value_width
    _write_line(
        screen, start_y + 1, start_x,
        f"{c['v']} {header_text} {c['v']} {empty_cell} {c['v']}",
    )
    _write_line(screen, start_y + 2, start_x, c["t_right"] + c["h"] * (name_width + 2) + c["cross"] + c["h"] * (value_width + 2) + c["t_left"])

    for i, (name, value) in enumerate(visible_rows):
        row_index = scroll_offset + i
        attr = curses.A_REVERSE if row_index == highlighted_index else 0
        row_y = start_y + 3 + i
        if row_y >= max_height - 1:
            break
        name_text = truncate(name, name_width).ljust(name_width)
        value_text = truncate(value, value_width).rjust(value_width)
        # 1 padding space on each side of both columns, matching the border's
        # h*(width+2) segments exactly, so every row's right edge lines up.
        _write_line(
            screen, row_y, start_x,
            f"{c['v']} {name_text} {c['v']} {value_text} {c['v']}", attr,
        )

    last_row = min(start_y + box_height - 1, max_height - 1)
    _write_line(screen, last_row, start_x, c["bl"] + c["h"] * (name_width + 2) + c["t_up"] + c["h"] * (value_width + 2) + c["br"])
