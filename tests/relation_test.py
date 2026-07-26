import datetime

import osmapi
import pytest
import responses
from responses import DELETE, GET, PUT
from responses.registries import OrderedRegistry

from .conftest import API_BASE, OPEN_CHANGESET_ID


def test_relation_get(api, add_response):
    resp = add_response(GET, "/relation/321")

    result = api.relation_get(321)

    assert resp.calls[0].request.method == "GET"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/relation/321"
    assert result == {
        "id": 321,
        "changeset": 434,
        "uid": 12,
        "timestamp": datetime.datetime(2009, 9, 15, 22, 24, 25),
        "visible": True,
        "version": 1,
        "user": "green525",
        "tag": {
            "admin_level": "9",
            "boundary": "administrative",
            "type": "multipolygon",
        },
        "member": [
            {"ref": 6908, "role": "outer", "type": "way"},
            {"ref": 6352, "role": "outer", "type": "way"},
            {"ref": 5669, "role": "outer", "type": "way"},
            {"ref": 5682, "role": "outer", "type": "way"},
            {"ref": 6909, "role": "outer", "type": "way"},
            {"ref": 6355, "role": "outer", "type": "way"},
            {"ref": 6910, "role": "outer", "type": "way"},
            {"ref": 6911, "role": "outer", "type": "way"},
            {"ref": 6912, "role": "outer", "type": "way"},
        ],
    }


def test_relation_get_with_version(api, add_response):
    resp = add_response(GET, "/relation/765/2")

    result = api.relation_get(765, 2)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/relation/765/2"
    assert result["id"] == 765
    assert result["changeset"] == 41378
    assert result["user"] == "metaodi"
    assert result["tag"]["source"] == "test"


def test_relation_create(changeset_api, add_response, assert_request_xml):
    resp = add_response(PUT, "/relation/create")
    test_relation = {
        "tag": {"type": "test"},
        "member": [
            {"ref": 6908, "role": "outer", "type": "way"},
            {"ref": 6352, "role": "point", "type": "node"},
        ],
    }

    result = changeset_api.relation_create(test_relation)

    assert resp.calls[0].request.method == "PUT"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/relation/create"
    assert_request_xml(
        resp.calls[0].request,
        f'<relation visible="true" changeset="{OPEN_CHANGESET_ID}">'
        '<tag k="type" v="test"/>'
        '<member type="way" ref="6908" role="outer"/>'
        '<member type="node" ref="6352" role="point"/>'
        "</relation>",
    )

    assert result["id"] == 8989
    assert result["version"] == 1
    assert result["member"] == test_relation["member"]
    assert result["tag"] == test_relation["tag"]


def test_relation_create_existing_node(changeset_api):
    test_relation = {
        "id": 456,
        "tag": {"type": "test"},
        "member": [{"ref": 6908, "role": "outer", "type": "way"}],
    }

    with pytest.raises(
        osmapi.OsmTypeAlreadyExistsError, match="This relation already exists"
    ):
        changeset_api.relation_create(test_relation)


def test_relation_update(changeset_api, add_response, assert_request_xml):
    resp = add_response(PUT, "/relation/8989")
    test_relation = {
        "id": 8989,
        "tag": {"type": "test update"},
        "member": [{"ref": 6908, "role": "outer", "type": "way"}],
    }

    result = changeset_api.relation_update(test_relation)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/relation/8989"
    assert_request_xml(
        resp.calls[0].request,
        f'<relation id="8989" visible="true" changeset="{OPEN_CHANGESET_ID}">'
        '<tag k="type" v="test update"/>'
        '<member type="way" ref="6908" role="outer"/>'
        "</relation>",
    )

    assert result["id"] == 8989
    assert result["version"] == 42
    assert result["member"] == test_relation["member"]
    assert result["tag"] == test_relation["tag"]


def test_relation_delete(changeset_api, add_response, assert_request_xml):
    resp = add_response(DELETE, "/relation/8989")

    result = changeset_api.relation_delete({"id": 8989})

    assert resp.calls[0].request.method == "DELETE"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/relation/8989"
    assert_request_xml(
        resp.calls[0].request,
        f'<relation id="8989" visible="true" changeset="{OPEN_CHANGESET_ID}"/>',
    )

    assert result["id"] == 8989
    assert result["version"] == 43
    assert result["visible"] is False


def test_relation_history(api, add_response):
    resp = add_response(GET, "/relation/2470397/history")

    result = api.relation_history(2470397)

    assert resp.calls[0].request.url == (f"{API_BASE}/api/0.6/relation/2470397/history")
    assert len(result) == 2
    assert result[1]["id"] == 2470397
    assert result[1]["version"] == 1
    assert result[1]["tag"] == {
        "restriction": "only_straight_on",
        "type": "restriction",
    }
    assert result[2]["version"] == 2


def test_relation_relations(api, add_response):
    resp = add_response(GET, "/relation/1532552/relations")

    result = api.relation_relations(1532552)

    assert resp.calls[0].request.url == (
        f"{API_BASE}/api/0.6/relation/1532552/relations"
    )
    assert len(result) == 1
    assert result[0]["id"] == 1532553
    assert result[0]["version"] == 85
    assert len(result[0]["member"]) == 120
    assert result[0]["tag"]["type"] == "network"
    assert result[0]["tag"]["name"] == "Aargauischer Radroutennetz"


def test_relation_relations_unused_element(api, add_response):
    resp = add_response(GET, "/relation/1532552/relations")

    result = api.relation_relations(1532552)

    assert resp.calls[0].request.url == (
        f"{API_BASE}/api/0.6/relation/1532552/relations"
    )
    assert result == []


def test_relation_full(api, add_response):
    resp = add_response(GET, "/relation/2470397/full")

    result = api.relation_full(2470397)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/relation/2470397/full"
    assert len(result) == 11
    assert result[1]["data"]["id"] == 101142277
    assert result[1]["data"]["version"] == 8
    assert result[1]["type"] == "node"
    assert result[10]["data"]["id"] == 2470397
    assert result[10]["data"]["version"] == 2
    assert result[10]["type"] == "relation"


def test_relation_full_with_deleted_relation(api, add_response):
    add_response(GET, "/relation/2911456/full", body="", status=410)

    with pytest.raises(osmapi.ElementDeletedApiError) as execinfo:
        api.relation_full(2911456)

    assert execinfo.value.status == 410


def test_relation_full_recur(api, add_response):
    """Nested relations are resolved level by level: 100 -> 200 -> 300."""
    resp = add_response(
        GET, "/relation/100/full", filename="test_relation_full_recur_100.xml"
    )
    add_response(GET, "/relation/200/full", filename="test_relation_full_recur_200.xml")
    add_response(GET, "/relation/300/full", filename="test_relation_full_recur_300.xml")

    result = api.relation_full_recur(100)

    # one request per relation level, in breadth-first order
    assert [call.request.url for call in resp.calls] == [
        f"{API_BASE}/api/0.6/relation/100/full",
        f"{API_BASE}/api/0.6/relation/200/full",
        f"{API_BASE}/api/0.6/relation/300/full",
    ]

    # the concatenation of all three responses, in the order they were fetched
    assert [(elem["type"], elem["data"]["id"]) for elem in result] == [
        ("node", 1),
        ("way", 10),
        ("relation", 200),
        ("relation", 100),
        ("node", 2),
        ("relation", 300),
        ("relation", 200),
        ("node", 3),
        ("relation", 300),
    ]


def test_relation_full_recur_stops_on_cycle(api, file_content):
    """A relation cycle terminates instead of looping forever.

    Uses an ordered registry so each response can be consumed only once: if
    the cycle guard ever regresses, the third request fails immediately
    instead of spinning forever.
    """
    with responses.RequestsMock(registry=OrderedRegistry) as rsps:
        for relation_id in (400, 401):
            rsps.add(
                GET,
                f"{API_BASE}/api/0.6/relation/{relation_id}/full",
                body=file_content(f"test_relation_full_recur_cycle_{relation_id}.xml"),
            )

        result = api.relation_full_recur(400)

        # each relation in the cycle is fetched exactly once
        assert [call.request.url for call in rsps.calls] == [
            f"{API_BASE}/api/0.6/relation/400/full",
            f"{API_BASE}/api/0.6/relation/401/full",
        ]

    assert [(elem["type"], elem["data"]["id"]) for elem in result] == [
        ("relation", 401),
        ("relation", 400),
        ("relation", 400),
        ("relation", 401),
    ]


def test_relation_full_recur_single_level(api, add_response):
    """A relation without relation members needs a single request."""
    resp = add_response(
        GET, "/relation/300/full", filename="test_relation_full_recur_300.xml"
    )

    result = api.relation_full_recur(300)

    assert len(resp.calls) == 1
    assert [(elem["type"], elem["data"]["id"]) for elem in result] == [
        ("node", 3),
        ("relation", 300),
    ]


def test_relation_full_recur_deleted_relation(api, add_response):
    """A deleted relation on any level surfaces as ElementDeletedApiError."""
    add_response(GET, "/relation/100/full", filename="test_relation_full_recur_100.xml")
    add_response(GET, "/relation/200/full", body="", status=410)

    with pytest.raises(osmapi.ElementDeletedApiError) as execinfo:
        api.relation_full_recur(100)

    assert execinfo.value.status == 410


def test_relations_get(api, add_response):
    resp = add_response(GET, "/relations")

    result = api.relations_get([1532552, 1532553])

    assert resp.calls[0].request.url == (
        f"{API_BASE}/api/0.6/relations?relations=1532552,1532553"
    )
    assert len(result) == 2
    assert result[1532553]["id"] == 1532553
    assert result[1532553]["version"] == 85
    assert result[1532553]["user"] == "SimonPoole"
    assert result[1532552]["id"] == 1532552
    assert result[1532552]["visible"] is True
    assert result[1532552]["tag"]["route"] == "bicycle"
