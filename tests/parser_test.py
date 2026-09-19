"""Tests for the document parsers, independent of any API call."""

import datetime

import pytest

import osmapi
from osmapi import parser


def test_parse_osm(file_content):
    result = parser.parse_osm(file_content("test_way_full.xml").encode())

    assert len(result) == 17
    assert result[0] == {
        "type": "node",
        "data": {
            "id": 11949,
            "lat": 58.415759,
            "lon": 23.0982328,
            "timestamp": datetime.datetime(2009, 9, 14, 23, 23, 17),
            "uid": 12,
            "user": "green525",
            "visible": True,
            "version": 1,
            "changeset": 298,
            "tag": {},
        },
    }
    assert result[16]["type"] == "way"
    assert result[16]["data"]["id"] == 321


def test_parse_osm_rejects_a_document_that_is_not_osm(file_content):
    document = file_content("test_changeset_download.xml").encode()

    with pytest.raises(
        osmapi.XmlResponseInvalidError, match="expected a <osm> element"
    ):
        parser.parse_osm(document)


def test_parse_osc(file_content):
    result = parser.parse_osc(file_content("test_changeset_download.xml").encode())

    assert len(result) == 16
    assert [change["action"] for change in result[:3]] == [
        "create",
        "create",
        "create",
    ]
    assert result[1]["type"] == "node"
    assert result[1]["data"]["id"] == 4295668171
    assert result[1]["data"]["tag"] == {"highway": "traffic_signals"}


def test_parse_osc_rejects_a_document_that_is_not_osc(file_content):
    document = file_content("test_way_full.xml").encode()

    with pytest.raises(
        osmapi.XmlResponseInvalidError, match="expected a <osmChange> element"
    ):
        parser.parse_osc(document)


def test_parse_notes(file_content):
    result = parser.parse_notes(file_content("test_notes_get.xml").encode())

    assert len(result) == 14
    assert result[0]["id"] == "231776"
    assert result[0]["status"] == "closed"
    assert result[0]["date_created"] == datetime.datetime(2014, 8, 28, 19, 27, 13)
    assert result[0]["date_closed"] == datetime.datetime(2014, 9, 27, 9, 27, 48)
    assert result[0]["comments"][0]["action"] == "opened"
