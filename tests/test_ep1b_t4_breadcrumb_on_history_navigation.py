from dbbro.config.models import Table
from dbbro.history.history import History
from dbbro.navigation.breadcrumb import Breadcrumb, BreadcrumbStop
from dbbro.ui import keys
from dbbro.ui.app import handle_navigation_keys
from dbbro.ui.table_view import TableView
from dbbro.ui.view_stack import ViewStack


def _table(name, pk="id"):
    return Table(name=name, columns=(pk,), primary_key=pk, search_columns=())


def _build_chain(breadcrumb, history):
    """Builds a 3-deep drill chain (Company -> Employee -> Shop), pushing a
    breadcrumb stop and a history entry at each step, mirroring how
    TableView._build_table_view really drills into a relation."""
    company = _table("Company")
    breadcrumb.push(BreadcrumbStop(table="Company", primary_key_value="1"))
    view_a = TableView(company, {"id": "1"}, conn=None, config=None, breadcrumb=breadcrumb)
    history.add_entry(view_a)

    employee = _table("Employee")
    breadcrumb.push(BreadcrumbStop(table="Employee", primary_key_value="9"))
    view_b = TableView(employee, {"id": "9"}, conn=None, config=None, breadcrumb=breadcrumb)
    history.add_entry(view_b)

    shop = _table("Shop")
    breadcrumb.push(BreadcrumbStop(table="Shop", primary_key_value="543334"))
    view_c = TableView(shop, {"id": "543334"}, conn=None, config=None, breadcrumb=breadcrumb)
    history.add_entry(view_c)

    return view_a, view_b, view_c


def test_breadcrumb_restores_full_path_on_left():
    history = History()
    breadcrumb = Breadcrumb()
    view_a, view_b, view_c = _build_chain(breadcrumb, history)
    stack = ViewStack(view_c)

    handle_navigation_keys(keys.LEFT, stack, history, breadcrumb)

    assert stack.current is view_b
    assert breadcrumb.as_list() == [
        BreadcrumbStop(table="Company", primary_key_value="1"),
        BreadcrumbStop(table="Employee", primary_key_value="9"),
    ]


def test_breadcrumb_restores_full_path_on_left_twice():
    history = History()
    breadcrumb = Breadcrumb()
    view_a, view_b, view_c = _build_chain(breadcrumb, history)
    stack = ViewStack(view_c)

    handle_navigation_keys(keys.LEFT, stack, history, breadcrumb)
    handle_navigation_keys(keys.LEFT, stack, history, breadcrumb)

    assert stack.current is view_a
    assert breadcrumb.as_list() == [BreadcrumbStop(table="Company", primary_key_value="1")]


def test_breadcrumb_restores_full_path_on_right():
    history = History()
    breadcrumb = Breadcrumb()
    view_a, view_b, view_c = _build_chain(breadcrumb, history)
    stack = ViewStack(view_c)
    handle_navigation_keys(keys.LEFT, stack, history, breadcrumb)
    handle_navigation_keys(keys.LEFT, stack, history, breadcrumb)

    handle_navigation_keys(keys.RIGHT, stack, history, breadcrumb)

    assert stack.current is view_b
    assert breadcrumb.as_list() == [
        BreadcrumbStop(table="Company", primary_key_value="1"),
        BreadcrumbStop(table="Employee", primary_key_value="9"),
    ]
