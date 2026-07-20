from dbbro.navigation.breadcrumb import Breadcrumb, BreadcrumbStop


def test_breadcrumb_push_appends_stop():
    breadcrumb = Breadcrumb()

    breadcrumb.push(BreadcrumbStop(table="Company", primary_key_value="1"))

    assert breadcrumb.as_list() == [BreadcrumbStop(table="Company", primary_key_value="1")]


def test_breadcrumb_as_list_ends_with_current_record():
    breadcrumb = Breadcrumb()
    breadcrumb.push(BreadcrumbStop(table="Company", primary_key_value="1"))
    breadcrumb.push(BreadcrumbStop(table="Employee", primary_key_value="9"))

    assert breadcrumb.as_list()[-1] == BreadcrumbStop(table="Employee", primary_key_value="9")


def test_breadcrumb_reset_clears_stops():
    breadcrumb = Breadcrumb()
    breadcrumb.push(BreadcrumbStop(table="Company", primary_key_value="1"))

    breadcrumb.reset()

    assert breadcrumb.as_list() == []
