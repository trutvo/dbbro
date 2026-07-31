import curses

from .breadcrumb_bar import render_breadcrumb_line
from .help_bar import HelpKey, render_help_line
from .relation_rows import DisplayRow

TOP_RESERVED_ROWS = 2

MODAL_CHARS = {
    "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
    "h": "═", "v": "║", "cross": "╬", "t_down": "╦", "t_up": "╩",
    "t_right": "╠", "t_left": "╣",
}
SECTION_BOX_CHARS = {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"}


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


def _usable_height(screen) -> int:
    """The terminal's height minus the bottom row, which is always
    reserved for the help bar (N3/AC7), so draw_panel/draw_modal never
    write into it."""
    max_height, _ = screen.getmaxyx()
    return max_height - 1


def _center_origin(box_width: int, box_height: int, max_width: int, max_height: int) -> tuple[int, int]:
    """Returns (start_y, start_x) so a box_width x box_height box is centered
    in the terminal, clamped to (TOP_RESERVED_ROWS, 0) if it wouldn't
    otherwise fit, so the top-reserved rows are never drawn over."""
    start_y = max(TOP_RESERVED_ROWS, (max_height - box_height) // 2)
    start_x = max(0, (max_width - box_width) // 2)
    return start_y, start_x


def draw_breadcrumb_bar(screen, stops: list) -> None:
    """Draws the breadcrumb at row 0, fitted to the terminal's current
    width. Row 1 is left blank, so the screen body starts on row 2 with a
    visible gap below the breadcrumb."""
    _, max_width = screen.getmaxyx()
    line = render_breadcrumb_line(stops, max_width)
    _write_line(screen, 0, 0, line)


def draw_modal(screen, lines: list[str], highlighted_index: int | None = None) -> None:
    """Draws a double-line modal box around `lines`, sized to the longest
    line (truncated to the terminal's current width), centered in the
    terminal, reverse-videoing the line at `highlighted_index` if given."""
    max_height, max_width = screen.getmaxyx()
    max_height = _usable_height(screen)
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
    last_row = max(start_y, min(start_y + box_height - 1, max_height - 1))
    _write_line(screen, last_row, start_x, c["bl"] + c["h"] * (box_width - 2) + c["br"])


def _full_width_text(row: DisplayRow) -> str:
    return row.value


def _section_top_border(title: str, width: int) -> str:
    c = SECTION_BOX_CHARS
    prefix = f"{c['tl']}{c['h']} {title} "
    if len(prefix) + 1 >= width:
        return truncate(prefix, max(0, width - 1)) + c["tr"]
    return prefix + c["h"] * (width - len(prefix) - 1) + c["tr"]


def _section_bottom_border(width: int) -> str:
    c = SECTION_BOX_CHARS
    return c["bl"] + c["h"] * max(0, width - 2) + c["br"]


def _section_body_line(text: str, width: int, attr: int) -> tuple[str, int]:
    c = SECTION_BOX_CHARS
    interior = max(0, width - 4)
    content = truncate(text, interior).ljust(interior)
    return f"{c['v']} {content} {c['v']}", attr


def _split_into_sections(rows: list[DisplayRow]) -> list[tuple[str, list[tuple[int, DisplayRow]]]]:
    """Groups `rows` by their preceding "section" row: each section's title
    (its value, stripped of indentation) paired with the (index, row) pairs
    of every row up to the next "section" row. Any rows preceding the first
    "section" row (not expected from build_display_rows, but possible from
    ad-hoc row lists) are kept, boxed under an empty title, rather than
    silently dropped."""
    sections: list[tuple[str, list[tuple[int, DisplayRow]]]] = []
    title = ""
    body: list[tuple[int, DisplayRow]] = []
    started = False
    for i, row in enumerate(rows):
        if row.kind == "section":
            if started or body:
                sections.append((title, body))
            title = row.value.strip()
            body = []
            started = True
        else:
            body.append((i, row))
    if started or body:
        sections.append((title, body))
    return sections


def _build_section_lines(
    rows: list[DisplayRow], highlighted_index: int, width: int
) -> tuple[list[tuple[str, int]], dict[int, int], dict[int, int]]:
    """Renders `rows` as one box per section: a top border with the
    section's title embedded, one bordered line per row (name_width scoped
    to that section's own field/reference rows), a bottom border, and a
    blank line before the next section. Returns the rendered (text, attr)
    lines, a row-index -> line-index map, and a row-index -> line-index map
    for rows that are the first row of their section (pointing at that
    section's own top-border line, so scrolling to a section's first row can
    reveal its border too)."""
    sections = _split_into_sections(rows)
    lines: list[tuple[str, int]] = []
    row_line_index: dict[int, int] = {}
    section_top_line_index: dict[int, int] = {}
    for section_i, (title, body) in enumerate(sections):
        top_line = len(lines)
        lines.append((_section_top_border(title, width), curses.A_BOLD))
        two_col = [r for _, r in body if r.kind in ("field", "reference")]
        name_width = max((len(r.name) for r in two_col), default=0)
        for row_i, (index, row) in enumerate(body):
            if row_i == 0:
                section_top_line_index[index] = top_line
            row_line_index[index] = len(lines)
            attr = curses.A_REVERSE if index == highlighted_index else 0
            if row.kind in ("field", "reference"):
                text = f"{row.name.ljust(name_width)}  {row.value}"
            else:
                text = _full_width_text(row)
            lines.append(_section_body_line(text, width, attr))
        lines.append((_section_bottom_border(width), 0))
        if section_i < len(sections) - 1:
            lines.append((" " * width, 0))
    return lines, row_line_index, section_top_line_index


def content_fits(rows: list[DisplayRow], screen) -> bool:
    """True if every rendered line for `rows` (including box borders and the
    blank lines between sections) fits within the screen's current usable
    body height (below TOP_RESERVED_ROWS, above the help bar) without
    needing to scroll."""
    max_height, max_width = screen.getmaxyx()
    max_height = _usable_height(screen)
    visible_height = max(0, max_height - TOP_RESERVED_ROWS)
    lines, _, _ = _build_section_lines(rows, -1, max_width)
    return len(lines) <= visible_height


def draw_panel(
    screen,
    rows: list[DisplayRow],
    highlighted_index: int,
    scroll_offset: int,
) -> None:
    """Draws each section (as split by "section"-kind rows) in its own
    single-line box, full terminal width, starting at TOP_RESERVED_ROWS,
    with the section's title embedded in its top border and one blank line
    between boxes. The first section's own title carries whatever text its
    row holds (e.g. the table name, for the Fields section) — there is no
    separate header line above the boxes. "field"/"reference" rows print as
    `name` left-padded to the widest name in that section, two spaces, then
    `value`; "group"/"related" rows print their full-width text in the
    plain attribute. The row at `highlighted_index` is reverse-videoed within
    its box's interior (never over the border characters). Scrolling starts
    rendering at the line for the row at `scroll_offset`, including that
    row's own section's top border only when `scroll_offset` is the first
    row of its section — otherwise a box may render truncated, with no top
    or bottom border visible, which is acceptable."""
    max_height, max_width = screen.getmaxyx()
    max_height = _usable_height(screen)
    start_y, start_x = TOP_RESERVED_ROWS, 0

    lines, row_line_index, section_top_line_index = _build_section_lines(rows, highlighted_index, max_width)

    visible_height = max(0, max_height - start_y)

    start_line = 0
    if rows:
        start_row = min(scroll_offset, len(rows) - 1)
        start_line = section_top_line_index.get(start_row, row_line_index.get(start_row, 0))

    visible_lines = lines[start_line : start_line + visible_height]
    for i, (text, attr) in enumerate(visible_lines):
        row_y = start_y + i
        if row_y >= max_height:
            break
        _write_line(screen, row_y, start_x, text, attr)


def draw_help_bar(screen, keys: list[HelpKey]) -> None:
    """Draws the one-line navigation help summary at the terminal's last
    row (N3/AC7), fitted to the terminal's current width, dropping
    lowest-priority keys first if the full list would otherwise overflow
    (F5/AC5)."""
    max_height, max_width = screen.getmaxyx()
    line = render_help_line(keys, max_width)
    _write_line(screen, max_height - 1, 0, line)
