from dbbro.history.history import History


def test_go_back_then_go_forward_returns_to_the_entry_left_via_back():
    history = History()
    history.add_entry("view-a")
    history.add_entry("view-b")
    history.add_entry("view-c")

    left_via_back = history.go_back()  # moves from "view-c" to "view-b"
    history.go_back()  # moves from "view-b" to "view-a"
    returned = history.go_forward()  # should return to "view-b"

    assert returned.view == left_via_back.view == "view-b"


def test_go_back_returns_the_entry_immediately_preceding_current():
    history = History()
    history.add_entry("view-a")
    history.add_entry("view-b")

    preceding = history.go_back()

    assert preceding.view == "view-a"
