import datetime
import logging
from unittest import mock

import osmapi


def test_dom_get_attributes():
    mock_domelement = mock.Mock()
    mock_domelement.attributes = {
        "uid": "12345",
        "open": "false",
        "visible": "true",
        "lat": "47.1234",
        "date": "2021-12-10T21:28:03Z",
        "new_attribute": "Test 123",
    }

    result = osmapi.dom._dom_get_attributes(mock_domelement)

    assert isinstance(result, dict)
    assert result["uid"] == 12345
    assert result["open"] is False
    assert result["visible"] is True
    assert result["lat"] == 47.1234
    assert result["date"] == datetime.datetime(2021, 12, 10, 21, 28, 3)
    assert result["new_attribute"] == "Test 123"


def test_parse_date():
    assert osmapi.dom._parse_date("2021-02-25T09:49:33Z") == datetime.datetime(
        2021, 2, 25, 9, 49, 33
    )
    assert osmapi.dom._parse_date("2021-02-25 09:49:33 UTC") == datetime.datetime(
        2021, 2, 25, 9, 49, 33
    )


def test_parse_date_unparsable_value_is_returned_unchanged(caplog):
    with caplog.at_level(logging.DEBUG, logger="osmapi.dom"):
        assert osmapi.dom._parse_date("2021-02-25") == "2021-02-25"
        assert osmapi.dom._parse_date("") == ""
        assert osmapi.dom._parse_date(None) is None

    assert [(r.levelname, r.name, r.getMessage()) for r in caplog.records] == [
        ("DEBUG", "osmapi.dom", "2021-02-25 does not match %Y-%m-%d %H:%M:%S UTC"),
        ("DEBUG", "osmapi.dom", "2021-02-25 does not match %Y-%m-%dT%H:%M:%SZ"),
        ("DEBUG", "osmapi.dom", " does not match %Y-%m-%d %H:%M:%S UTC"),
        ("DEBUG", "osmapi.dom", " does not match %Y-%m-%dT%H:%M:%SZ"),
        ("DEBUG", "osmapi.dom", "None does not match %Y-%m-%d %H:%M:%S UTC"),
        ("DEBUG", "osmapi.dom", "None does not match %Y-%m-%dT%H:%M:%SZ"),
    ]
