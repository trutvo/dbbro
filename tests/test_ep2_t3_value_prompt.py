from dbbro.ui import keys
from dbbro.ui.search_prompt import SearchValuePrompt
from dbbro.ui.view_stack import Transition, TransitionKind


def test_value_prompt_appends_typed_characters_to_buffer():
    prompt = SearchValuePrompt("Company", "name")

    for ch in "Acme":
        prompt.handle_key(ord(ch))

    assert prompt.buffer == "Acme"


def test_return_with_empty_buffer_is_rejected_no_transition():
    prompt = SearchValuePrompt("Company", "name")

    transition = prompt.handle_key(keys.RETURN)

    assert transition is None


def test_return_with_nonempty_buffer_triggers_lookup(two_table_config, sqlite_conn):
    sqlite_conn.execute("INSERT INTO Company VALUES ('1', 'Acme')")
    prompt = SearchValuePrompt(
        "Company", "name", conn=sqlite_conn, config=two_table_config
    )
    for ch in "Acme":
        prompt.handle_key(ord(ch))

    transition = prompt.handle_key(keys.RETURN)

    assert transition.kind is TransitionKind.PUSH
    assert transition.view.record == {"id": "1", "name": "Acme"}


def test_escape_in_value_prompt_pops_to_selection_dialog_no_lookup():
    prompt = SearchValuePrompt("Company", "name")
    prompt.handle_key(ord("A"))

    transition = prompt.handle_key(keys.ESCAPE)

    assert transition == Transition.pop()
