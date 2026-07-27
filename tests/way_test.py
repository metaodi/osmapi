import datetime

import osmapi
import pytest
from responses import DELETE, GET, PUT

from .conftest import API_BASE, OPEN_CHANGESET_ID


def test_way_get(api, add_response):
    resp = add_response(GET, "/way/321")

    result = api.way_get(321)

    assert resp.calls[0].request.method == "GET"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/way/321"
    assert result == {
        "id": 321,
        "changeset": 298,
        "uid": 12,
        "timestamp": datetime.datetime(2009, 9, 14, 23, 23, 18),
        "visible": True,
        "version": 1,
        "user": "green525",
        "tag": {"admin_level": "9", "boundary": "administrative"},
        "nd": [
            11949,
            11950,
            11951,
            11952,
            11953,
            11954,
            11955,
            11956,
            11957,
            11958,
            11959,
            11960,
            11961,
            11962,
            11963,
            11964,
            11949,
        ],
    }


def test_way_get_with_version(api, add_response):
    resp = add_response(GET, "/way/4294967296/2")

    result = api.way_get(4294967296, 2)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/way/4294967296/2"
    assert result["id"] == 4294967296
    assert result["changeset"] == 41303
    assert result["user"] == "metaodi"


def test_way_get_nodata(api, add_response):
    add_response(GET, "/way/321")

    with pytest.raises(osmapi.ResponseEmptyApiError):
        api.way_get(321)


def test_way_create(changeset_api, add_response, assert_request_xml):
    resp = add_response(PUT, "/way/create")
    test_way = {
        "nd": [11949, 11950],
        "tag": {"highway": "unclassified", "name": "Osmapi Street"},
    }

    result = changeset_api.way_create(test_way)

    assert resp.calls[0].request.method == "PUT"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/way/create"
    assert_request_xml(
        resp.calls[0].request,
        f'<way visible="true" changeset="{OPEN_CHANGESET_ID}">'
        '<tag k="highway" v="unclassified"/>'
        '<tag k="name" v="Osmapi Street"/>'
        '<nd ref="11949"/>'
        '<nd ref="11950"/>'
        "</way>",
    )

    assert result["id"] == 5454
    assert result["version"] == 1
    assert result["nd"] == test_way["nd"]
    assert result["tag"] == test_way["tag"]


def test_way_create_existing_node(changeset_api):
    test_way = {
        "id": 456,
        "nd": [11949, 11950],
        "tag": {"highway": "unclassified", "name": "Osmapi Street"},
    }

    with pytest.raises(
        osmapi.OsmTypeAlreadyExistsError, match="This way already exists"
    ):
        changeset_api.way_create(test_way)


def test_way_update(changeset_api, add_response, assert_request_xml):
    resp = add_response(PUT, "/way/876")
    test_way = {
        "id": 876,
        "nd": [11949, 11950],
        "tag": {"highway": "unclassified", "name": "Osmapi Street Update"},
    }

    result = changeset_api.way_update(test_way)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/way/876"
    assert_request_xml(
        resp.calls[0].request,
        f'<way id="876" visible="true" changeset="{OPEN_CHANGESET_ID}">'
        '<tag k="highway" v="unclassified"/>'
        '<tag k="name" v="Osmapi Street Update"/>'
        '<nd ref="11949"/>'
        '<nd ref="11950"/>'
        "</way>",
    )

    assert result["id"] == 876
    assert result["version"] == 7
    assert result["nd"] == test_way["nd"]
    assert result["tag"] == test_way["tag"]


def test_way_update_precondition_failed(changeset_api, add_response):
    add_response(PUT, "/way/876", status=412)
    test_way = {
        "id": 876,
        "nd": [11949, 11950],
        "tag": {"highway": "unclassified", "name": "Osmapi Street Update"},
    }

    with pytest.raises(osmapi.PreconditionFailedApiError) as execinfo:
        changeset_api.way_update(test_way)

    assert execinfo.value.status == 412
    assert execinfo.value.payload_str == (
        "Way 876 requires the nodes with id in (11950), "
        "which either do not exist, or are not visible."
    )


def test_way_delete(changeset_api, add_response, assert_request_xml):
    resp = add_response(DELETE, "/way/876")

    result = changeset_api.way_delete({"id": 876})

    assert resp.calls[0].request.method == "DELETE"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/way/876"
    assert_request_xml(
        resp.calls[0].request,
        f'<way id="876" visible="true" changeset="{OPEN_CHANGESET_ID}"/>',
    )

    assert result["id"] == 876
    assert result["version"] == 8
    assert result["visible"] is False


def test_way_history(api, add_response):
    resp = add_response(GET, "/way/4294967296/history")

    result = api.way_history(4294967296)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/way/4294967296/history"
    assert len(result) == 2
    assert result[1]["id"] == 4294967296
    assert result[1]["version"] == 1
    assert result[1]["tag"] == {
        "highway": "unclassified",
        "name": "Stansted Road",
    }


def test_way_relations(api, add_response):
    resp = add_response(GET, "/way/4295032193/relations")

    result = api.way_relations(4295032193)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/way/4295032193/relations"
    assert len(result) == 1
    assert result[0]["id"] == 4294968148
    assert result[0]["changeset"] == 23123
    assert result[0]["member"][4] == {"role": "", "ref": 4295032193, "type": "way"}
    assert result[0]["tag"] == {"type": "fancy"}


def test_way_relations_unused_element(api, add_response):
    resp = add_response(GET, "/way/4295032193/relations")

    result = api.way_relations(4295032193)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/way/4295032193/relations"
    assert result == []


def test_way_full(api, add_response):
    resp = add_response(GET, "/way/321/full")

    result = api.way_full(321)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/way/321/full"
    assert len(result) == 17
    assert result[0]["data"]["id"] == 11949
    assert result[0]["data"]["changeset"] == 298
    assert result[0]["type"] == "node"
    assert result[16]["data"]["id"] == 321
    assert result[16]["data"]["changeset"] == 298
    assert result[16]["type"] == "way"


def test_way_full_invalid_response(api, add_response):
    add_response(GET, "/way/321/full")

    with pytest.raises(osmapi.XmlResponseInvalidError):
        api.way_full(321)


def test_ways_get(api, add_response):
    resp = add_response(GET, "/ways")

    result = api.ways_get([456, 678])

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/ways?ways=456,678"
    assert len(result) == 2
    assert isinstance(result[456], dict)
    assert isinstance(result[678], dict)
    with pytest.raises(KeyError):
        result[123]
