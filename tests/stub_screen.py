class StubScreen:
    """Fake curses window recording addstr calls, for headless rendering tests."""

    def __init__(self, height=24, width=80):
        self._height = height
        self._width = width
        self.calls = []

    def getmaxyx(self):
        return (self._height, self._width)

    def addstr(self, y, x, text, attr=0):
        self.calls.append((y, x, text, attr))

    def erase(self):
        self.calls.append("erase")

    def all_text(self):
        return "".join(c[2] for c in self.calls if isinstance(c, tuple))
