import datetime
import io
import logging
import tracemalloc
from xml.etree.ElementTree import Element

import pytest

import osmapi

OSM = b'<osm version="0.6"><node id="1"><tag k="a" v="b"/></node><node id="2"/></osm>'


def test_iter_elements_yields_matching_elements():
    result = [
        (parent, element.attrib["id"])
        for parent, element in osmapi.dom._iter_elements(OSM, ("node",))
    ]

    assert result == [("osm", "1"), ("osm", "2")]


def test_iter_elements_releases_every_element_it_has_passed():
    """An element is emptied again once iteration moves on.

    That is what keeps the memory needed for a response independent of its
    size, and it is why a yielded element has to be consumed before the next
    one is requested.
    """
    seen = []
    for _, element in osmapi.dom._iter_elements(OSM, ("node",)):
        # the element currently yielded still carries all of its data ...
        assert element.attrib
        seen.append(element)
        # ... while every element handed out before it is empty
        assert all(not (previous.attrib or list(previous)) for previous in seen[:-1])

    assert len(seen) == 2
    assert all(not (element.attrib or list(element)) for element in seen)


def test_iter_elements_memory_is_independent_of_document_size():
    """The parsed document never accumulates, however many elements it has."""
    count = 20000
    document = io.BytesIO(
        b'<osm version="0.6">'
        + b'<node id="1" lat="47.1" lon="8.5" version="3"/>' * count
        + b"</osm>"
    )

    tracemalloc.start()
    try:
        parsed = sum(1 for _ in osmapi.dom._iter_elements(document, ("node",)))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert parsed == count
    # Keeping the elements around costs ~100 bytes each, i.e. megabytes here;
    # streaming needs the read buffer and a single element.
    assert peak < 500_000


def test_iter_elements_rejects_a_wrong_root_element():
    with pytest.raises(
        osmapi.XmlResponseInvalidError, match="expected a <osm> element"
    ):
        list(osmapi.dom._iter_elements(b"<osmChange/>", ("node",), root_tag="osm"))


def test_iter_elements_reports_malformed_xml():
    with pytest.raises(osmapi.XmlResponseInvalidError, match="ParseError"):
        list(osmapi.dom._iter_elements(b"<osm><node/>", ("node",)))


def test_osm_response_to_dom_single_keeps_the_element_intact():
    """`single` stops parsing early, so the element is not released."""
    element = osmapi.dom.OsmResponseToDom(OSM, tag="node", single=True)

    assert element.attrib == {"id": "1"}
    assert [tag.attrib for tag in element] == [{"k": "a", "v": "b"}]


def test_osm_response_to_dom_without_a_matching_element():
    with pytest.raises(
        osmapi.XmlResponseInvalidError, match="contains no <way> element"
    ):
        osmapi.dom.OsmResponseToDom(OSM, tag="way", single=True)

    with pytest.raises(
        osmapi.XmlResponseInvalidError, match="contains no <way> element"
    ):
        list(osmapi.dom.OsmResponseToDom(OSM, tag="way"))

    assert list(osmapi.dom.OsmResponseToDom(OSM, tag="way", allow_empty=True)) == []


def test_dom_get_attributes():
    element = Element("node")
    element.attrib = {
        "uid": "12345",
        "open": "false",
        "visible": "true",
        "lat": "47.1234",
        "date": "2021-12-10T21:28:03Z",
        "new_attribute": "Test 123",
    }

    result = osmapi.dom._dom_get_attributes(element)

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
