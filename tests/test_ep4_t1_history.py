from dbbro.history.history import History


def test_new_history_is_empty_and_current_is_none():
    history = History()

    assert history.current() is None


def test_add_entry_appends_and_becomes_current():
    history = History()

    entry = history.add_entry("view-a")

    assert history.current() is entry
    assert entry.view == "view-a"


def test_add_entry_always_adds_even_for_identical_snapshot():
    history = History()
    history.add_entry("view-a")

    second = history.add_entry("view-a")

    assert history.current() is second


def test_add_entry_after_go_back_truncates_forward_entries():
    history = History()
    history.add_entry("view-a")
    history.add_entry("view-b")
    history.go_back()

    history.add_entry("view-c")

    assert history.current().view == "view-c"
    assert history.go_forward() is None


def test_go_back_at_earliest_entry_returns_none_and_position_unchanged():
    history = History()
    entry = history.add_entry("view-a")

    assert history.go_back() is None
    assert history.current() is entry


def test_go_forward_at_latest_entry_returns_none_and_position_unchanged():
    history = History()
    entry = history.add_entry("view-a")

    assert history.go_forward() is None
    assert history.current() is entry


def test_history_has_no_size_limit():
    history = History()

    for i in range(500):
        history.add_entry(f"view-{i}")

    assert history.current().view == "view-499"
