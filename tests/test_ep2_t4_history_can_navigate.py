from dbbro.history.history import History


def test_can_go_back_false_when_at_start():
    history = History()
    history.add_entry(object())

    assert history.can_go_back() is False


def test_can_go_back_true_after_multiple_entries():
    history = History()
    history.add_entry(object())
    history.add_entry(object())

    assert history.can_go_back() is True


def test_can_go_forward_false_at_most_recent_entry():
    history = History()
    history.add_entry(object())
    history.add_entry(object())

    assert history.can_go_forward() is False


def test_can_go_forward_true_after_going_back():
    history = History()
    history.add_entry(object())
    history.add_entry(object())
    history.go_back()

    assert history.can_go_forward() is True
