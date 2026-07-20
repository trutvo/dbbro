from dbbro.config.models import Config
from dbbro.history.history import History
from dbbro.navigation.breadcrumb import Breadcrumb
from dbbro.search.models import MultipleMatches, SingleMatch
from dbbro.ui.app import build_view_stack
from dbbro.ui.search_dialog import SearchSelectionDialog
from dbbro.ui.selection_list import SelectionList
from dbbro.ui.table_view import TableView
from types import MappingProxyType


def test_build_view_stack_defaults_to_search_dialog_when_no_initial_outcome():
    config = Config(tables=MappingProxyType({}))

    stack = build_view_stack(config)

    assert isinstance(stack.current, SearchSelectionDialog)


def test_build_view_stack_opens_directly_on_table_view_for_single_match():
    from dbbro.config.models import Table

    table = Table(name="Company", columns=("id", "name"), primary_key="id")
    config = Config(tables=MappingProxyType({"Company": table}))
    outcome = SingleMatch(table="Company", record={"id": "1", "name": "Acme"})
    history = History()
    breadcrumb = Breadcrumb()

    stack = build_view_stack(
        config, breadcrumb=breadcrumb, history=history, initial_outcome=outcome
    )

    assert isinstance(stack.current, TableView)
    assert history.current() is not None


def test_build_view_stack_opens_directly_on_selection_list_for_multiple_matches():
    from dbbro.config.models import Table

    table = Table(name="Company", columns=("id", "name"), primary_key="id")
    config = Config(tables=MappingProxyType({"Company": table}))
    outcome = MultipleMatches(
        table="Company",
        records=[{"id": "1", "name": "Acme"}, {"id": "2", "name": "Beta"}],
    )

    stack = build_view_stack(config, initial_outcome=outcome)

    assert isinstance(stack.current, SelectionList)
