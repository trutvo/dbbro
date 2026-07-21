from ..navigation.breadcrumb import BreadcrumbStop

TOP_LEVEL_LABEL = "Tables"
SEPARATOR = " > "


def _fit_to_width(text: str, width: int) -> str:
    """Truncates `text` to `width`, keeping its head and tail visible and
    replacing the middle with an ellipsis."""
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    ellipsis = "..."
    remaining = width - len(ellipsis)
    head = (remaining + 1) // 2
    tail = remaining - head
    return text[:head] + ellipsis + (text[len(text) - tail :] if tail else "")


def render_breadcrumb_line(stops: list[BreadcrumbStop], width: int) -> str:
    """Returns TOP_LEVEL_LABEL if `stops` is empty; otherwise the full
    navigation path, each stop rendered as "{table}[{primary_key_value}]"
    and joined with " > ". If the full path doesn't fit `width`, the middle
    stops are collapsed to "..." while the first and last stops stay
    visible; if even that doesn't fit, the result is truncated by
    character, keeping head and tail visible."""
    if width <= 0:
        return ""
    if not stops:
        return _fit_to_width(TOP_LEVEL_LABEL, width)

    segments = [f"{stop.table}[{stop.primary_key_value}]" for stop in stops]
    full_text = SEPARATOR.join(segments)
    if len(full_text) <= width:
        return full_text

    if len(segments) > 2:
        collapsed = SEPARATOR.join([segments[0], "...", segments[-1]])
        if len(collapsed) <= width:
            return collapsed
        return _fit_to_width(collapsed, width)

    return _fit_to_width(full_text, width)
