"""Tests for the XML generated for write requests."""

import xml.etree.ElementTree as ET

import pytest

import osmapi
from osmapi import xmlbuilder

from .conftest import API_BASE, OPEN_CHANGESET_ID


@pytest.fixture
def build(changeset_api):
    """Builds the XML for an element write and parses it back."""

    def _build(element_type, element_data, with_headers=True):
        xml = xmlbuilder._xml_build(
            element_type, element_data, with_headers, data=changeset_api
        )
        assert isinstance(xml, bytes)
        return xml, ET.fromstring(xml)

    return _build


def test_xml_build_wraps_the_element_in_an_osm_envelope(build):
    xml, root = build("node", {"id": 1, "lat": 47.1, "lon": 8.5, "version": 3})

    assert xml.startswith(b'<?xml version="1.0" encoding="UTF-8"?>')
    assert root.tag == "osm"
    assert root.attrib == {
        "version": "0.6",
        "generator": f"osmapi/{osmapi.__version__}",
    }
    assert list(root[0].attrib) == [
        "id",
        "lat",
        "lon",
        "version",
        "visible",
        "changeset",
    ]
    assert root[0].attrib["changeset"] == str(OPEN_CHANGESET_ID)


def test_xml_build_without_headers_returns_the_bare_element(build):
    xml, element = build("way", {"id": 2, "nd": [11, 12]}, with_headers=False)

    assert not xml.startswith(b"<?xml")
    assert element.tag == "way"
    assert [nd.attrib["ref"] for nd in element] == ["11", "12"]


def test_xml_build_defaults_visible_to_true(build):
    _, root = build("node", {"id": 1})
    assert root[0].attrib["visible"] == "true"

    _, root = build("node", {"id": 1, "visible": False})
    assert root[0].attrib["visible"] == "false"


def test_xml_build_only_sets_changeset_on_elements(build):
    """A `<changeset>` is not itself part of a changeset."""
    _, root = build("changeset", {"tag": {"comment": "hello"}})

    assert "changeset" not in root[0].attrib


def test_xml_build_escapes_markup(build):
    value = 'a & b <c> "d"'
    _, root = build("node", {"id": 1, "tag": {"key": value}})

    assert root[0][0].attrib == {"k": "key", "v": value}


def test_xml_build_preserves_whitespace_in_values(build):
    """Newlines and tabs survive the round trip (issue #216).

    An XML parser normalizes literal newlines and tabs in an attribute value
    to spaces, so they have to be written as character references. Escaping
    only `& " < >` by hand silently corrupted such values on their way to the
    API.
    """
    tags = {"note": "line one\nline two", "ref": "A\tB", "cr": "a\rb"}
    xml, root = build("node", {"id": 1, "tag": tags})

    assert b"&#10;" in xml
    assert {tag.attrib["k"]: tag.attrib["v"] for tag in root[0]} == tags


def test_xml_build_escapes_member_attributes(build):
    member = {"type": "way", "ref": 9, "role": 'a"b\nc'}
    _, root = build("relation", {"id": 1, "member": [member]})

    assert root[0][0].attrib == {"type": "way", "ref": "9", "role": 'a"b\nc'}


def test_xml_build_handles_unicode(build):
    xml, root = build("node", {"id": 1, "tag": {"name": "Zürich 東京"}})

    assert "Zürich 東京".encode("utf-8") in xml
    assert root[0][0].attrib["v"] == "Zürich 東京"


def test_node_update_sends_whitespace_in_tags_unharmed(changeset_api, add_response):
    """The same round trip, over the wire this time."""
    resp = add_response("PUT", "/node/876", body="7")

    changeset_api.node_update(
        {"id": 876, "lat": 47.1, "lon": 8.5, "tag": {"note": "first\nsecond"}}
    )

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/876"
    sent = ET.fromstring(resp.calls[0].request.body)
    assert sent[0][0].attrib == {"k": "note", "v": "first\nsecond"}
