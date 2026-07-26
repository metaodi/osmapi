import datetime

import osmapi
import pytest
from requests.auth import HTTPBasicAuth
from responses import DELETE, GET, PUT

from .conftest import API_BASE, OPEN_CHANGESET_ID

TEST_NODE = {
    "lat": 47.287,
    "lon": 8.765,
    "tag": {"amenity": "place_of_worship", "religion": "pastafarian"},
}


def test_node_get(api, add_response):
    resp = add_response(GET, "/node/123")

    result = api.node_get(123)

    assert resp.calls[0].request.method == "GET"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/123"
    assert result == {
        "id": 123,
        "changeset": 15293,
        "uid": 605,
        "timestamp": datetime.datetime(2012, 4, 18, 11, 14, 26),
        "lat": 51.8753146,
        "lon": -1.4857118,
        "visible": True,
        "version": 8,
        "user": "freundchen",
        "tag": {"amenity": "school", "foo": "bar", "name": "Berolina & Schule"},
    }


def test_node_get_with_version(api, add_response):
    resp = add_response(GET, "/node/123/2")

    result = api.node_get(123, node_version=2)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/123/2"
    assert result == {
        "id": 123,
        "changeset": 4152,
        "uid": 605,
        "timestamp": datetime.datetime(2011, 4, 18, 11, 14, 26),
        "lat": 51.8753146,
        "lon": -1.4857118,
        "visible": True,
        "version": 2,
        "user": "freundchen",
        "tag": {"amenity": "school"},
    }


def test_node_get_invalid_response(api, add_response):
    add_response(GET, "/node/987")

    with pytest.raises(osmapi.XmlResponseInvalidError):
        api.node_get(987)


def test_node_create(changeset_api, add_response, assert_request_xml):
    resp = add_response(PUT, "/node/create")

    result = changeset_api.node_create(dict(TEST_NODE))

    assert resp.calls[0].request.method == "PUT"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/create"
    assert_request_xml(
        resp.calls[0].request,
        f'<node lat="47.287" lon="8.765" visible="true" '
        f'changeset="{OPEN_CHANGESET_ID}">'
        '<tag k="amenity" v="place_of_worship"/>'
        '<tag k="religion" v="pastafarian"/>'
        "</node>",
    )

    assert result["id"] == 9876
    assert result["version"] == 1
    assert result["changeset"] == OPEN_CHANGESET_ID
    assert result["lat"] == TEST_NODE["lat"]
    assert result["lon"] == TEST_NODE["lon"]
    assert result["tag"] == TEST_NODE["tag"]


def test_node_create_wo_changeset(auth_api):
    with pytest.raises(osmapi.NoChangesetOpenError, match="need to open a changeset"):
        auth_api.node_create(dict(TEST_NODE))


def test_node_create_existing_node(changeset_api):
    test_node = dict(TEST_NODE, id=123)

    with pytest.raises(
        osmapi.OsmTypeAlreadyExistsError, match="This node already exists"
    ):
        changeset_api.node_create(test_node)


def test_node_create_wo_auth(api):
    api._current_changeset_id = OPEN_CHANGESET_ID

    with pytest.raises(
        osmapi.UsernamePasswordMissingError, match="Username/Password missing"
    ):
        api.node_create(dict(TEST_NODE))


def test_node_create_unauthorized(changeset_api, add_response):
    add_response(PUT, "/node/create", body="", status=401)

    with pytest.raises(osmapi.UnauthorizedApiError):
        changeset_api.node_create(dict(TEST_NODE))


def test_node_create_with_session_auth(mock_api):
    api, session = mock_api(auth=False, content="3322")
    session.auth = HTTPBasicAuth("user", "pass")
    api = osmapi.OsmApi(api=API_BASE, session=session)
    api._current_changeset_id = OPEN_CHANGESET_ID

    result = api.node_create(dict(TEST_NODE))

    assert result["id"] == 3322


def test_node_create_with_exception(mock_api):
    api, session = mock_api(side_effect=Exception)
    api._current_changeset_id = OPEN_CHANGESET_ID

    with pytest.raises(
        osmapi.MaximumRetryLimitReachedError, match="Give up after 5 retries"
    ):
        api.node_create(dict(TEST_NODE))


def test_node_create_drops_timestamp(changeset_api, add_response, assert_request_xml):
    """`_do` strips a client-supplied timestamp, the server assigns its own."""
    resp = add_response(PUT, "/node/create", filename="test_node_create.xml")
    test_node = dict(TEST_NODE, timestamp=datetime.datetime(2012, 4, 18, 11, 14, 26))

    result = changeset_api.node_create(test_node)

    assert "timestamp" not in resp.calls[0].request.body.decode("utf-8")
    assert "timestamp" not in result
    assert_request_xml(
        resp.calls[0].request,
        f'<node lat="47.287" lon="8.765" visible="true" '
        f'changeset="{OPEN_CHANGESET_ID}">'
        '<tag k="amenity" v="place_of_worship"/>'
        '<tag k="religion" v="pastafarian"/>'
        "</node>",
    )


def test_node_update(changeset_api, add_response, assert_request_xml):
    resp = add_response(PUT, "/node/7676")
    test_node = {
        "id": 7676,
        "lat": 47.287,
        "lon": 8.765,
        "tag": {"amenity": "place_of_worship", "name": "christian"},
    }

    result = changeset_api.node_update(test_node)

    assert resp.calls[0].request.method == "PUT"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/7676"
    assert_request_xml(
        resp.calls[0].request,
        f'<node id="7676" lat="47.287" lon="8.765" visible="true" '
        f'changeset="{OPEN_CHANGESET_ID}">'
        '<tag k="amenity" v="place_of_worship"/>'
        '<tag k="name" v="christian"/>'
        "</node>",
    )

    assert result["id"] == 7676
    assert result["version"] == 3
    assert result["lat"] == test_node["lat"]
    assert result["lon"] == test_node["lon"]
    assert result["tag"] == test_node["tag"]


def test_node_update_when_changeset_is_closed(changeset_api, add_response):
    add_response(PUT, "/node/7676", status=409)
    test_node = {"id": 7676, "lat": 47.287, "lon": 8.765, "tag": {}}

    with pytest.raises(osmapi.ChangesetClosedApiError) as execinfo:
        changeset_api.node_update(test_node)

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload
        == b"The changeset 2222 was closed at 2021-11-20 09:42:47 UTC."
    )
    assert (
        execinfo.value.payload_str
        == "The changeset 2222 was closed at 2021-11-20 09:42:47 UTC."
    )


def test_node_update_conflict(changeset_api, add_response):
    add_response(PUT, "/node/7676", status=409)
    test_node = {"id": 7676, "lat": 47.287, "lon": 8.765, "tag": {}}

    with pytest.raises(osmapi.VersionMismatchApiError) as execinfo:
        changeset_api.node_update(test_node)

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload
        == b"Version does not match the current database version of the element"
    )


def test_node_delete(changeset_api, add_response, assert_request_xml):
    resp = add_response(DELETE, "/node/7676")

    result = changeset_api.node_delete({"id": 7676})

    assert resp.calls[0].request.method == "DELETE"
    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/7676"
    assert_request_xml(
        resp.calls[0].request,
        f'<node id="7676" visible="true" changeset="{OPEN_CHANGESET_ID}"/>',
    )

    assert result["id"] == 7676
    assert result["version"] == 4
    # a deleted element is reported back as no longer visible
    assert result["visible"] is False


def test_node_delete_when_changeset_is_closed(changeset_api, add_response):
    add_response(DELETE, "/node/7676", status=409)

    with pytest.raises(osmapi.ChangesetClosedApiError) as execinfo:
        changeset_api.node_delete({"id": 7676})

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload_str
        == "The changeset 1111 was closed at 2024-03-01 10:00:00 UTC."
    )


def test_node_delete_conflict(changeset_api, add_response):
    add_response(DELETE, "/node/7676", status=409)

    with pytest.raises(osmapi.VersionMismatchApiError) as execinfo:
        changeset_api.node_delete({"id": 7676})

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload_str
        == "Version does not match the current database version of the element"
    )


def test_node_delete_precondition_failed(changeset_api, add_response):
    add_response(DELETE, "/node/7676", status=412)

    with pytest.raises(osmapi.PreconditionFailedApiError) as execinfo:
        changeset_api.node_delete({"id": 7676})

    assert execinfo.value.status == 412
    assert execinfo.value.payload_str == "Node 7676 is still used by ways 1234."


def test_node_delete_forbidden(changeset_api, add_response):
    """A status the write-error translation does not special-case is re-raised."""
    add_response(DELETE, "/node/7676", status=403)

    with pytest.raises(osmapi.ApiError) as execinfo:
        changeset_api.node_delete({"id": 7676})

    assert type(execinfo.value) is osmapi.ApiError
    assert execinfo.value.status == 403


def test_node_create_when_changeset_is_closed(changeset_api, add_response):
    add_response(PUT, "/node/create", status=409)

    with pytest.raises(osmapi.ChangesetClosedApiError) as execinfo:
        changeset_api.node_create(dict(TEST_NODE))

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload_str
        == "The changeset 1111 was closed at 2024-03-01 10:00:00 UTC."
    )


def test_node_create_precondition_failed(changeset_api, add_response):
    add_response(PUT, "/node/create", status=412)

    with pytest.raises(osmapi.PreconditionFailedApiError) as execinfo:
        changeset_api.node_create(dict(TEST_NODE))

    assert execinfo.value.status == 412


def test_node_history(api, add_response):
    resp = add_response(GET, "/node/123/history")

    result = api.node_history(123)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/123/history"
    assert len(result) == 8
    assert result[4]["id"] == 123
    assert result[4]["version"] == 4
    assert result[4]["lat"] == 51.8753146
    assert result[4]["lon"] == -1.4857118
    assert result[4]["tag"] == {"empty": "", "foo": "bar"}


def test_node_ways(api, add_response):
    resp = add_response(GET, "/node/234/ways")

    result = api.node_ways(234)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/234/ways"
    assert len(result) == 1
    assert result[0]["id"] == 60
    assert result[0]["changeset"] == 61
    assert result[0]["tag"] == {"highway": "path", "name": "Dog walking path"}


def test_node_ways_not_exists(api, add_response):
    resp = add_response(GET, "/node/404/ways")

    result = api.node_ways(404)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/404/ways"
    assert result == []


def test_node_relations(api, add_response):
    resp = add_response(GET, "/node/4295668179/relations")

    result = api.node_relations(4295668179)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/4295668179/relations"
    assert len(result) == 1
    assert result[0]["id"] == 4294968148
    assert result[0]["changeset"] == 23123
    assert result[0]["member"][1] == {
        "role": "point",
        "ref": 4295668179,
        "type": "node",
    }
    assert result[0]["tag"] == {"type": "fancy"}


def test_node_relations_unused_element(api, add_response):
    resp = add_response(GET, "/node/4295668179/relations")

    result = api.node_relations(4295668179)

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/node/4295668179/relations"
    assert result == []


def test_nodes_get(api, add_response):
    resp = add_response(GET, "/nodes")

    result = api.nodes_get([123, 345])

    assert resp.calls[0].request.url == f"{API_BASE}/api/0.6/nodes?nodes=123,345"
    assert len(result) == 2
    assert result[123] == {
        "id": 123,
        "changeset": 15293,
        "uid": 605,
        "timestamp": datetime.datetime(2012, 4, 18, 11, 14, 26),
        "lat": 51.8753146,
        "lon": -1.4857118,
        "visible": True,
        "version": 8,
        "user": "freundchen",
        "tag": {"amenity": "school", "foo": "bar", "name": "Berolina & Schule"},
    }
    assert result[345] == {
        "id": 345,
        "changeset": 244,
        "timestamp": datetime.datetime(2009, 9, 12, 3, 22, 59),
        "uid": 1,
        "visible": False,
        "version": 2,
        "user": "guggis",
        "tag": {},
    }
