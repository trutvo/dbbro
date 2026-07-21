from dbbro.navigation.breadcrumb import BreadcrumbStop
from dbbro.ui.breadcrumb_bar import render_breadcrumb_line


def test_empty_stops_returns_root_label():
    assert render_breadcrumb_line([], 80) == "Tables"


def test_single_stop_formats_table_and_primary_key():
    stops = [BreadcrumbStop(table="Shop", primary_key_value="543334")]
    assert render_breadcrumb_line(stops, 80) == "Shop[543334]"


def test_multiple_stops_shows_full_path():
    stops = [
        BreadcrumbStop(table="Membership", primary_key_value="1"),
        BreadcrumbStop(table="Shop", primary_key_value="543334"),
    ]
    assert render_breadcrumb_line(stops, 80) == "Membership[1] > Shop[543334]"


def test_long_path_collapses_middle_stops_keeping_first_and_last():
    stops = [
        BreadcrumbStop(table="Membership", primary_key_value="1"),
        BreadcrumbStop(table="Company", primary_key_value="2"),
        BreadcrumbStop(table="Shop", primary_key_value="543334"),
    ]
    result = render_breadcrumb_line(stops, 40)
    assert result == "Membership[1] > ... > Shop[543334]"


def test_truncates_long_line_keeping_head_and_tail():
    stops = [BreadcrumbStop(table="VeryLongTableName", primary_key_value="9999999999")]
    full = "VeryLongTableName[9999999999]"
    result = render_breadcrumb_line(stops, 10)
    assert len(result) <= 10
    assert result[:3] == full[:3]
    assert result[-3:] == full[-3:]


def test_zero_width_returns_empty_string():
    stops = [BreadcrumbStop(table="Shop", primary_key_value="543334")]
    assert render_breadcrumb_line(stops, 0) == ""
