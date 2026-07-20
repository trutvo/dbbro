from dbbro.navigation.breadcrumb import Breadcrumb, BreadcrumbStop
from dbbro.ui import keys
from dbbro.ui.search_prompt import SearchValuePrompt
from dbbro.ui.table_view import TableView


def test_single_match_search_result_is_a_real_table_view(two_table_config, sqlite_conn):
    sqlite_conn.execute("INSERT INTO Company VALUES ('1', 'Acme')")
    breadcrumb = Breadcrumb()
    prompt = SearchValuePrompt(
        "Company", "name", conn=sqlite_conn, config=two_table_config, breadcrumb=breadcrumb
    )
    for ch in "Acme":
        prompt.handle_key(ord(ch))

    transition = prompt.handle_key(keys.RETURN)

    assert isinstance(transition.view, TableView)
    assert breadcrumb.as_list() == [BreadcrumbStop(table="Company", primary_key_value="1")]


def test_new_search_resets_breadcrumb(two_table_config, sqlite_conn):
    sqlite_conn.execute("INSERT INTO Company VALUES ('1', 'Acme')")
    sqlite_conn.execute("INSERT INTO Company VALUES ('2', 'Beta')")
    breadcrumb = Breadcrumb()
    breadcrumb.push(BreadcrumbStop(table="Stale", primary_key_value="0"))

    prompt = SearchValuePrompt(
        "Company", "name", conn=sqlite_conn, config=two_table_config, breadcrumb=breadcrumb
    )
    for ch in "Acme":
        prompt.handle_key(ord(ch))
    prompt.handle_key(keys.RETURN)

    assert breadcrumb.as_list() == [BreadcrumbStop(table="Company", primary_key_value="1")]
