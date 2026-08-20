import osmapi
import xmltodict
import datetime
import pytest
from responses import GET, PUT, POST
import requests

from .conftest import GENERATOR


def xmltosorteddict(xml):
    xml_dict = xmltodict.parse(xml, dict_constructor=dict)
    return xml_dict


def test_changeset_contextmanager(auth_api, add_response):
    # Setup mock
    resp = add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    resp = add_response(PUT, "/node/create", filename="test_changeset_create_node.xml")
    resp = add_response(
        PUT, "/changeset/1414/close", filename="test_changeset_close.xml"
    )

    test_node = {
        "lat": 47.123,
        "lon": 8.555,
        "tag": {"amenity": "place_of_worship", "religion": "pastafarian"},
    }

    # use context manager
    with auth_api.changeset() as changeset_id:
        assert changeset_id == 1414

        # add test node
        node = auth_api.node_create(test_node)
        assert node["id"] == 7272

    # check requests
    assert len(resp.calls) == 3


def test_changeset_get(api, add_response):
    # Setup mock
    add_response(GET, "/changeset/123")
    # Call
    result = api.changeset_get(123)
    test_changeset = {
        "id": 123,
        "closed_at": datetime.datetime(2009, 9, 7, 22, 57, 37),
        "created_at": datetime.datetime(2009, 9, 7, 21, 57, 36),
        "max_lat": "52.4710193",
        "max_lon": "-1.4831815",
        "min_lat": "45.9667901",
        "min_lon": "-1.4998534",
        "open": False,
        "user": "randomjunk",
        "uid": 3,
        "tag": {
            "comment": "correct node bug",
            "created_by": "Potlatch 1.2a",
        },
    }
    assert result == test_changeset


def test_changeset_get_with_connection_error(api, add_response):
    # Setup mock
    add_response(
        GET,
        "/changeset/123",
        body=requests.exceptions.ConnectionError("Connection aborted."),
    )

    # Call
    with pytest.raises(osmapi.ConnectionApiError) as execinfo:
        api.changeset_get(123)
    assert (
        str(execinfo.value)
        == "Request failed: 0 - Connection error: Connection aborted. - "
    )


def test_changeset_get_with_timeout(api, add_response):
    # Setup mock
    add_response(GET, "/changeset/123", body=requests.exceptions.Timeout())

    # Call
    with pytest.raises(osmapi.TimeoutApiError) as execinfo:
        api.changeset_get(123)
    assert (
        str(execinfo.value) == "Request failed: 0 - Request timed out (timeout=30) - "
    )


def test_changeset_update(auth_api, add_response):
    # Setup mock
    resp = add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    resp = add_response(PUT, "/changeset/1414", filename="test_changeset_update.xml")

    # Call
    result = auth_api.changeset_create()
    assert result == 1414

    result = auth_api.changeset_update({"test": "foobar"})
    changeset_xml = xmltosorteddict(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<osm version="0.6" generator="{GENERATOR}">\n'
        '  <changeset visible="true">\n'
        '    <tag k="test" v="foobar"/>\n'
        f'    <tag k="created_by" v="{GENERATOR}"/>\n'
        "  </changeset>\n"
        "</osm>\n"
    )
    assert xmltosorteddict(resp.calls[1].request.body) == changeset_xml
    assert result == 1414


def test_changeset_update_with_created_by(auth_api, add_response):
    # Setup mock
    resp = add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    resp = add_response(PUT, "/changeset/1414", filename="test_changeset_update.xml")

    # Call
    result = auth_api.changeset_create()
    assert result == 1414

    result = auth_api.changeset_update({"test": "foobar", "created_by": "MyTestOSMApp"})
    changeset_xml = xmltosorteddict(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<osm version="0.6" generator="{GENERATOR}">\n'
        '  <changeset visible="true">\n'
        '    <tag k="test" v="foobar"/>\n'
        '    <tag k="created_by" v="MyTestOSMApp"/>\n'
        "  </changeset>\n"
        "</osm>\n"
    )
    assert xmltosorteddict(resp.calls[1].request.body) == changeset_xml
    assert result == 1414


def test_changeset_update_wo_changeset(auth_api):
    with pytest.raises(osmapi.NoChangesetOpenError) as execinfo:
        auth_api.changeset_update({"test": "foobar"})
    assert str(execinfo.value) == "No changeset currently opened"


def test_changeset_create(auth_api, add_response):
    resp = add_response(PUT, "/changeset/create")
    result = auth_api.changeset_create({"foobar": "A new test changeset"})
    assert result == 1414

    changeset_xml = xmltosorteddict(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<osm version="0.6" generator="{GENERATOR}">\n'
        '  <changeset visible="true">\n'
        '    <tag k="foobar" v="A new test changeset"/>\n'
        f'    <tag k="created_by" v="{GENERATOR}"/>\n'
        "  </changeset>\n"
        "</osm>\n"
    )
    assert xmltosorteddict(resp.calls[0].request.body) == changeset_xml


def test_changeset_create_with_created_by(auth_api, add_response):
    resp = add_response(PUT, "/changeset/create")

    result = auth_api.changeset_create(
        {
            "foobar": "A new test changeset",
            "created_by": "CoolTestApp",
        }
    )
    assert result == 1234

    changeset_xml = xmltosorteddict(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<osm version="0.6" generator="{GENERATOR}">\n'
        '  <changeset visible="true">\n'
        '    <tag k="foobar" v="A new test changeset"/>\n'
        '    <tag k="created_by" v="CoolTestApp"/>\n'
        "  </changeset>\n"
        "</osm>\n"
    )
    assert xmltosorteddict(resp.calls[0].request.body) == changeset_xml


def test_changeset_create_with_open_changeset(auth_api, add_response):
    add_response(PUT, "/changeset/create")

    auth_api.changeset_create(
        {
            "test": "an already open changeset",
        }
    )

    with pytest.raises(osmapi.ChangesetAlreadyOpenError) as execinfo:
        auth_api.changeset_create({"test": "foobar"})
    assert str(execinfo.value) == "Changeset already opened"


def test_changeset_create_with_prod_api_and_test_comment(prod_api):
    with pytest.raises(osmapi.OsmApiError) as execinfo:
        prod_api.changeset_create(
            {
                "comment": "My first test",
            }
        )
    assert (
        str(execinfo.value) == "DO NOT CREATE test changesets on the production server"
    )


def test_changeset_close(auth_api, add_response):
    # setup mock
    resp = add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    resp = add_response(PUT, "/changeset/1414/close")

    # Call
    auth_api.changeset_create()
    auth_api.changeset_close()

    assert "/api/0.6/changeset/1414/close" in resp.calls[1].request.url


def test_changeset_close_with_no_changeset(auth_api):
    with pytest.raises(osmapi.NoChangesetOpenError) as execinfo:
        auth_api.changeset_close()
    assert str(execinfo.value) == "No changeset currently opened"


def test_changeset_upload_create_node(auth_api, add_response):
    # Setup
    resp = add_response(PUT, "/changeset/create", body="4444")
    resp = add_response(POST, "/changeset/4444/upload")

    changesdata = [
        {
            "type": "node",
            "action": "create",
            "data": [
                {
                    "lat": 47.123,
                    "lon": 8.555,
                    "tag": {"amenity": "place_of_worship", "religion": "pastafarian"},
                },
                {
                    "lat": 47.125,
                    "lon": 8.557,
                    "tag": {"amenity": "place_of_worship", "religion": "pastafarian"},
                },
            ],
        }
    ]

    upload_xml = xmltosorteddict(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<osmChange version="0.6" generator="{GENERATOR}">\n'
        "<create>\n"
        '  <node lat="47.123" lon="8.555" visible="true" '
        'changeset="4444">\n'
        '    <tag k="amenity" v="place_of_worship"/>\n'
        '    <tag k="religion" v="pastafarian"/>\n'
        "  </node>\n"
        '  <node lat="47.125" lon="8.557" visible="true" '
        'changeset="4444">\n'
        '    <tag k="amenity" v="place_of_worship"/>\n'
        '    <tag k="religion" v="pastafarian"/>\n'
        "  </node>\n"
        "</create>\n"
        "</osmChange>"
    )

    # Call
    auth_api.changeset_create()
    result = auth_api.changeset_upload(changesdata)

    # Assert
    assert xmltosorteddict(resp.calls[1].request.body) == upload_xml
    assert result[0]["type"] == changesdata[0]["type"]
    assert result[0]["action"] == changesdata[0]["action"]

    data = result[0]["data"]
    assert data[0]["lat"] == changesdata[0]["data"][0]["lat"]
    assert data[0]["lon"] == changesdata[0]["data"][0]["lon"]
    assert data[0]["tag"] == changesdata[0]["data"][0]["tag"]
    assert data[0]["id"] == 4295832900
    assert result[0]["data"][0]["version"] == 1


def test_changeset_upload_modify_way(auth_api, add_response):
    # setup mock
    resp = add_response(PUT, "/changeset/create", body="4444")
    resp = add_response(POST, "/changeset/4444/upload")

    changesdata = [
        {
            "type": "way",
            "action": "modify",
            "data": [
                {
                    "id": 4294967296,
                    "version": 2,
                    "nd": [
                        4295832773,
                        4295832773,
                        4294967304,
                        4294967303,
                        4294967300,
                        4608751,
                        4294967305,
                        4294967302,
                        8548430,
                        4294967296,
                        4294967301,
                        4294967298,
                        4294967306,
                        7855737,
                        4294967297,
                        4294967299,
                    ],
                    "tag": {"highway": "secondary", "name": "Stansted Road"},
                }
            ],
        }
    ]

    upload_xml = xmltosorteddict(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<osmChange version="0.6" generator="{GENERATOR}">\n'
        "<modify>\n"
        '  <way id="4294967296" version="2" visible="true" '
        'changeset="4444">\n'
        '    <tag k="highway" v="secondary"/>\n'
        '    <tag k="name" v="Stansted Road"/>\n'
        '    <nd ref="4295832773"/>\n'
        '    <nd ref="4295832773"/>\n'
        '    <nd ref="4294967304"/>\n'
        '    <nd ref="4294967303"/>\n'
        '    <nd ref="4294967300"/>\n'
        '    <nd ref="4608751"/>\n'
        '    <nd ref="4294967305"/>\n'
        '    <nd ref="4294967302"/>\n'
        '    <nd ref="8548430"/>\n'
        '    <nd ref="4294967296"/>\n'
        '    <nd ref="4294967301"/>\n'
        '    <nd ref="4294967298"/>\n'
        '    <nd ref="4294967306"/>\n'
        '    <nd ref="7855737"/>\n'
        '    <nd ref="4294967297"/>\n'
        '    <nd ref="4294967299"/>\n'
        "  </way>\n"
        "</modify>\n"
        "</osmChange>"
    )

    # Call
    auth_api.changeset_create()
    result = auth_api.changeset_upload(changesdata)
    # Assert
    assert xmltosorteddict(resp.calls[1].request.body) == upload_xml

    assert result[0]["type"] == changesdata[0]["type"]
    assert result[0]["action"] == changesdata[0]["action"]

    data = result[0]["data"][0]
    print(data)
    assert data["nd"] == changesdata[0]["data"][0]["nd"]
    assert data["tag"] == changesdata[0]["data"][0]["tag"]
    assert data["id"] == 4294967296
    assert data["version"] == 3


def test_changeset_upload_delete_relation(auth_api, add_response):
    # setup mock
    resp = add_response(PUT, "/changeset/create", body="4444")
    resp = add_response(POST, "/changeset/4444/upload")

    changesdata = [
        {
            "type": "relation",
            "action": "delete",
            "data": [
                {
                    "id": 676,
                    "version": 2,
                    "member": [
                        {"ref": 4799, "role": "outer", "type": "way"},
                        {"ref": 9391, "role": "outer", "type": "way"},
                    ],
                    "tag": {
                        "admin_level": "9",
                        "boundary": "administrative",
                        "type": "multipolygon",
                    },
                }
            ],
        }
    ]

    upload_xml = xmltosorteddict(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<osmChange version="0.6" generator="{GENERATOR}">\n'
        "<delete>\n"
        '  <relation id="676" version="2" visible="true" '
        'changeset="4444">\n'
        '    <tag k="admin_level" v="9"/>\n'
        '    <tag k="boundary" v="administrative"/>\n'
        '    <tag k="type" v="multipolygon"/>\n'
        '    <member type="way" ref="4799" role="outer"/>\n'
        '    <member type="way" ref="9391" role="outer"/>\n'
        "  </relation>\n"
        "</delete>\n"
        "</osmChange>"
    )

    # Call
    auth_api.changeset_create()
    result = auth_api.changeset_upload(changesdata)

    # Assert
    assert xmltosorteddict(resp.calls[1].request.body) == upload_xml
    assert result[0]["type"] == changesdata[0]["type"]
    assert result[0]["action"] == changesdata[0]["action"]

    data = result[0]["data"][0]
    assert data["member"], changesdata[0]["data"][0]["member"]
    assert data["tag"] == changesdata[0]["data"][0]["tag"]
    assert data["id"] == 676
    assert "version" not in data


def test_changeset_upload_invalid_response(auth_api, add_response):
    # setup mock
    add_response(PUT, "/changeset/create", body="4444")
    add_response(POST, "/changeset/4444/upload", body="4444")

    changesdata = [
        {
            "type": "relation",
            "action": "delete",
            "data": [
                {
                    "id": 676,
                    "version": 2,
                    "member": [
                        {"ref": 4799, "role": "outer", "type": "way"},
                        {"ref": 9391, "role": "outer", "type": "way"},
                    ],
                    "tag": {
                        "admin_level": "9",
                        "boundary": "administrative",
                        "type": "multipolygon",
                    },
                }
            ],
        }
    ]

    # Call + assert
    auth_api.changeset_create()
    with pytest.raises(osmapi.XmlResponseInvalidError) as execinfo:
        auth_api.changeset_upload(changesdata)
    assert "The XML response from the OSM API is invalid" in str(execinfo.value)


def test_changeset_upload_response_that_is_not_a_diff_result(auth_api, add_response):
    add_response(PUT, "/changeset/create", body="4444")
    add_response(POST, "/changeset/4444/upload", body="<osm version='0.6'/>")

    changesdata = [
        {
            "type": "node",
            "action": "create",
            "data": [{"lat": 47.123, "lon": 8.555, "tag": {}}],
        }
    ]

    auth_api.changeset_create()
    with pytest.raises(
        osmapi.XmlResponseInvalidError, match="expected a <diffResult> element"
    ):
        auth_api.changeset_upload(changesdata)


def test_changeset_upload_no_auth(api):
    changesdata = [
        {
            "type": "node",
            "action": "create",
            "data": [
                {
                    "lat": 47.123,
                    "lon": 8.555,
                    "tag": {"amenity": "place_of_worship", "religion": "pastafarian"},
                }
            ],
        }
    ]

    with pytest.raises(osmapi.AuthenticationMissingError) as execinfo:
        api.changeset_upload(changesdata)
    assert "Authentication missing" in str(execinfo.value)


def test_changeset_upload_version_mismatch_raises_api_error(auth_api, add_response):
    """HTTP 409 version mismatch must raise ApiError, not TypeError."""
    add_response(PUT, "/changeset/create", body="4444")
    add_response(
        POST,
        "/changeset/4444/upload",
        body=b"Version mismatch: Provided 3, server had: 4",
        status=409,
    )

    changesdata = [
        {
            "type": "node",
            "action": "modify",
            "data": [{"id": 1, "version": 3, "lat": 47.0, "lon": 8.0, "tag": {}}],
        }
    ]

    auth_api.changeset_create()
    with pytest.raises(osmapi.errors.ApiError) as execinfo:
        auth_api.changeset_upload(changesdata)
    assert execinfo.value.status == 409
    assert b"Version mismatch" in execinfo.value.payload


def test_changeset_upload_closed_changeset_raises_correct_error(auth_api, add_response):
    """HTTP 409 'changeset closed' must raise ChangesetClosedApiError."""
    add_response(PUT, "/changeset/create", body="4444")
    add_response(
        POST,
        "/changeset/4444/upload",
        body=b"The changeset 4444 was closed at 2024-01-01T00:00:00Z",
        status=409,
    )

    changesdata = [
        {
            "type": "node",
            "action": "modify",
            "data": [{"id": 1, "version": 1, "lat": 47.0, "lon": 8.0, "tag": {}}],
        }
    ]

    auth_api.changeset_create()
    with pytest.raises(osmapi.errors.ChangesetClosedApiError):
        auth_api.changeset_upload(changesdata)


def test_changeset_download(api, add_response):
    # Setup mock
    add_response(GET, "/changeset/23123/download")

    # Call
    result = api.changeset_download(23123)

    # Assertion
    assert len(result) == 16
    assert result[1] == (
        {
            "action": "create",
            "type": "node",
            "data": {
                "changeset": 23123,
                "id": 4295668171,
                "lat": 46.4909781,
                "lon": 11.2743295,
                "tag": {"highway": "traffic_signals"},
                "timestamp": datetime.datetime(2013, 5, 14, 10, 33, 4),
                "uid": 1178,
                "user": "tyrTester06",
                "version": 1,
                "visible": True,
            },
        }
    )


def test_changeset_download_iter(api, add_response):
    resp = add_response(
        GET, "/changeset/23123/download", filename="test_changeset_download.xml"
    )

    result = list(api.changeset_download_iter(23123))

    assert resp.calls[0].request.url == (
        "http://api06.dev.openstreetmap.org/api/0.6/changeset/23123/download"
    )
    assert len(result) == 16
    assert result[1] == (
        {
            "action": "create",
            "type": "node",
            "data": {
                "changeset": 23123,
                "id": 4295668171,
                "lat": 46.4909781,
                "lon": 11.2743295,
                "tag": {"highway": "traffic_signals"},
                "timestamp": datetime.datetime(2013, 5, 14, 10, 33, 4),
                "uid": 1178,
                "user": "tyrTester06",
                "version": 1,
                "visible": True,
            },
        }
    )


def test_changeset_download_invalid_response(api, add_response):
    add_response(GET, "/changeset/23123/download")
    with pytest.raises(osmapi.XmlResponseInvalidError) as execinfo:
        api.changeset_download(23123)
    assert "The XML response from the OSM API is invalid" in str(execinfo.value)


def test_changeset_download_containing_unicode(api, add_response):
    add_response(GET, "/changeset/37393499/download")

    # This changeset contains unicode tag values
    # Note that the fixture data has been reduced from the
    # original from openstreetmap.org
    result = api.changeset_download(37393499)

    assert len(result) == 2
    assert result[1] == (
        {
            "action": "create",
            "type": "way",
            "data": {
                "changeset": 37393499,
                "id": 399491497,
                "nd": [4022271571, 4022271567, 4022271565],
                "tag": {
                    "highway": "service",
                    # UTF-8 encoded 'LATIN SMALL LETTER O WITH STROKE'
                    # Aka. 0xf8 in latin-1/ISO 8859-1             Emoji: 😀
                    "name": b"S\xc3\xb8nderskovvej".decode("utf-8") + " \U0001f600",
                    "service": "driveway",
                },
                "timestamp": datetime.datetime(2016, 2, 23, 16, 55, 35),
                "uid": 328556,
                "user": "InternationalUser",
                "version": 1,
                "visible": True,
            },
        }
    )


def test_changesets_get(api, add_response):
    resp = add_response(GET, "/changesets")
    result = api.changesets_get(only_closed=True, username="metaodi")
    assert resp.calls[0].request.params == {"display_name": "metaodi", "closed": "1"}
    assert len(result) == 10
    assert result[41417] == (
        {
            "closed_at": datetime.datetime(2014, 4, 29, 20, 25, 1),
            "created_at": datetime.datetime(2014, 4, 29, 20, 25, 1),
            "id": 41417,
            "max_lat": "58.8997467",
            "max_lon": "22.7364427",
            "min_lat": "58.8501594",
            "min_lon": "22.6984333",
            "open": False,
            "tag": {
                "comment": "Test delete of relation",
                "created_by": "iD 1.3.9",
                "imagery_used": "Bing",
            },
            "uid": 1841,
            "user": "metaodi",
        }
    )


def test_changeset_get_with_comment(api, add_response):
    resp = add_response(GET, "/changeset/52924")

    result = api.changeset_get(52924, include_discussion=True)

    assert resp.calls[0].request.params == {"include_discussion": "true"}
    assert result == {
        "id": 52924,
        "closed_at": datetime.datetime(2015, 1, 1, 14, 54, 2),
        "created_at": datetime.datetime(2015, 1, 1, 14, 54, 1),
        "comments_count": 3,
        "max_lat": "58.3369242",
        "max_lon": "25.8829107",
        "min_lat": "58.336813",
        "min_lon": "25.8823273",
        "discussion": [
            {
                "date": datetime.datetime(2015, 1, 1, 18, 56, 48),
                "text": "test",
                "uid": 1841,
                "user": "metaodi",
            },
            {
                "date": datetime.datetime(2015, 1, 1, 18, 58, 3),
                "text": "another comment",
                "uid": 1841,
                "user": "metaodi",
            },
            {
                "date": datetime.datetime(2015, 1, 1, 19, 16, 5),
                "text": "hello",
                "uid": 1841,
                "user": "metaodi",
            },
        ],
        "open": False,
        "user": "metaodi",
        "uid": 1841,
        "tag": {
            "comment": "My test",
            "created_by": "osmapi/0.4.1",
        },
    }


def test_changeset_get_without_discussion(api, add_response):
    resp = add_response(GET, "/changeset/52924")

    result = api.changeset_get(52924, include_discussion=False)

    assert resp.calls[0].request.params == {}
    assert result == {
        "id": 52924,
        "closed_at": datetime.datetime(2015, 1, 1, 14, 54, 2),
        "created_at": datetime.datetime(2015, 1, 1, 14, 54, 1),
        "max_lat": "58.3369242",
        "max_lon": "25.8829107",
        "min_lat": "58.336813",
        "min_lon": "25.8823273",
        "open": False,
        "user": "metaodi",
        "uid": 1841,
        "tag": {
            "comment": "My test",
            "created_by": "osmapi/0.4.1",
        },
    }


def test_changeset_comment(auth_api, add_response):
    resp = add_response(POST, "/changeset/123/comment")

    result = auth_api.changeset_comment(123, comment="test comment")

    assert resp.calls[0].request.body == "text=test+comment"
    assert result == {
        "id": 123,
        "closed_at": datetime.datetime(2009, 9, 7, 22, 57, 37),
        "created_at": datetime.datetime(2009, 9, 7, 21, 57, 36),
        "max_lat": "52.4710193",
        "max_lon": "-1.4831815",
        "min_lat": "45.9667901",
        "min_lon": "-1.4998534",
        "open": False,
        "user": "randomjunk",
        "uid": 3,
        "tag": {
            "comment": "correct node bug",
            "created_by": "Potlatch 1.2a",
        },
    }


def test_changeset_comment_no_auth(api):
    with pytest.raises(osmapi.AuthenticationMissingError) as execinfo:
        api.changeset_comment(123, comment="test comment")
    assert "Authentication missing" in str(execinfo.value)


def test_changeset_subscribe(auth_api, add_response):
    add_response(POST, "/changeset/123/subscribe")

    result = auth_api.changeset_subscribe(123)

    assert result == {
        "id": 123,
        "closed_at": datetime.datetime(2009, 9, 7, 22, 57, 37),
        "created_at": datetime.datetime(2009, 9, 7, 21, 57, 36),
        "max_lat": "52.4710193",
        "max_lon": "-1.4831815",
        "min_lat": "45.9667901",
        "min_lon": "-1.4998534",
        "open": False,
        "user": "randomjunk",
        "uid": 3,
        "tag": {
            "comment": "correct node bug",
            "created_by": "Potlatch 1.2a",
        },
    }


def test_changeset_subscribe_when_already_subscribed(auth_api, add_response):
    add_response(POST, "/changeset/52924/subscribe", status=409)

    with pytest.raises(osmapi.AlreadySubscribedApiError) as execinfo:
        auth_api.changeset_subscribe(52924)

    assert execinfo.value.payload == b"You are already subscribed to changeset 52924."
    assert execinfo.value.reason == "Conflict"
    assert execinfo.value.status == 409


def test_changeset_subscribe_no_auth(api):
    with pytest.raises(osmapi.AuthenticationMissingError) as execinfo:
        api.changeset_subscribe(45627)
    assert "Authentication missing" in str(execinfo.value)


def test_changeset_unsubscribe(auth_api, add_response):
    add_response(POST, "/changeset/123/unsubscribe")

    result = auth_api.changeset_unsubscribe(123)

    assert result == {
        "id": 123,
        "closed_at": datetime.datetime(2009, 9, 7, 22, 57, 37),
        "created_at": datetime.datetime(2009, 9, 7, 21, 57, 36),
        "max_lat": "52.4710193",
        "max_lon": "-1.4831815",
        "min_lat": "45.9667901",
        "min_lon": "-1.4998534",
        "open": False,
        "user": "randomjunk",
        "uid": 3,
        "tag": {
            "comment": "correct node bug",
            "created_by": "Potlatch 1.2a",
        },
    }


def test_changeset_unsubscribe_when_not_subscribed(auth_api, add_response):
    add_response(POST, "/changeset/52924/unsubscribe", status=404)

    with pytest.raises(osmapi.NotSubscribedApiError) as execinfo:
        auth_api.changeset_unsubscribe(52924)

    assert execinfo.value.payload == b"You are not subscribed to changeset 52924."
    assert execinfo.value.reason == "Not Found"
    assert execinfo.value.status == 404


def test_changeset_unsubscribe_no_auth(api):
    with pytest.raises(osmapi.AuthenticationMissingError) as execinfo:
        api.changeset_unsubscribe(45627)
    assert "Authentication missing" in str(execinfo.value)


##################################################
# changesets_get query parameters                #
##################################################


def test_changesets_get_no_filters(api, add_response):
    resp = add_response(GET, "/changesets", filename="test_changesets_get.xml")

    api.changesets_get()

    assert resp.calls[0].request.url == (
        "http://api06.dev.openstreetmap.org/api/0.6/changesets"
    )


def test_changesets_get_by_userid(api, add_response):
    resp = add_response(GET, "/changesets", filename="test_changesets_get.xml")

    api.changesets_get(userid=1841)

    assert resp.calls[0].request.params == {"user": "1841"}


def test_changesets_get_only_open(api, add_response):
    resp = add_response(GET, "/changesets", filename="test_changesets_get.xml")

    api.changesets_get(only_open=True)

    assert resp.calls[0].request.params == {"open": "1"}


def test_changesets_get_bbox(api, add_response):
    resp = add_response(GET, "/changesets", filename="test_changesets_get.xml")

    api.changesets_get(min_lon=8.7, min_lat=47.2, max_lon=8.8, max_lat=47.3)

    assert resp.calls[0].request.params == {"bbox": "8.7,47.2,8.8,47.3"}


def test_changesets_get_bbox_at_origin(api, add_response):
    """A bbox of all zeros is a real bbox and must not be dropped."""
    resp = add_response(GET, "/changesets", filename="test_changesets_get.xml")

    api.changesets_get(min_lon=0, min_lat=0, max_lon=0, max_lat=0)

    assert resp.calls[0].request.params == {"bbox": "0,0,0,0"}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_lon": 8.7},
        {"min_lon": 8.7, "min_lat": 47.2},
        {"min_lon": 8.7, "min_lat": 47.2, "max_lon": 8.8},
        {"max_lat": 47.3},
    ],
)
def test_changesets_get_partial_bbox_raises(api, kwargs):
    """A partial bbox is rejected instead of being sent with 'None' in it."""
    with pytest.raises(ValueError, match="bounding box needs all of"):
        api.changesets_get(**kwargs)


def test_changesets_get_closed_after(api, add_response):
    resp = add_response(GET, "/changesets", filename="test_changesets_get.xml")

    api.changesets_get(closed_after="2024-01-01T00:00:00Z")

    assert resp.calls[0].request.params == {"time": "2024-01-01T00:00:00Z"}


def test_changesets_get_created_before(api, add_response):
    """`created_before` alone becomes a range starting at the epoch."""
    resp = add_response(GET, "/changesets", filename="test_changesets_get.xml")

    api.changesets_get(created_before="2024-06-01T00:00:00Z")

    assert resp.calls[0].request.params == {
        "time": "1970-01-01T00:00:00Z,2024-06-01T00:00:00Z"
    }


def test_changesets_get_time_range(api, add_response):
    resp = add_response(GET, "/changesets", filename="test_changesets_get.xml")

    api.changesets_get(
        closed_after="2024-01-01T00:00:00Z", created_before="2024-06-01T00:00:00Z"
    )

    assert resp.calls[0].request.params == {
        "time": "2024-01-01T00:00:00Z,2024-06-01T00:00:00Z"
    }


def test_changesets_get_all_filters(api, add_response):
    resp = add_response(GET, "/changesets", filename="test_changesets_get.xml")

    api.changesets_get(
        min_lon=8.7,
        min_lat=47.2,
        max_lon=8.8,
        max_lat=47.3,
        userid=1841,
        username="metaodi",
        closed_after="2024-01-01T00:00:00Z",
        created_before="2024-06-01T00:00:00Z",
        only_open=True,
        only_closed=True,
    )

    assert resp.calls[0].request.params == {
        "bbox": "8.7,47.2,8.8,47.3",
        "user": "1841",
        "display_name": "metaodi",
        "time": "2024-01-01T00:00:00Z,2024-06-01T00:00:00Z",
        "open": "1",
        "closed": "1",
    }


##################################################
# Error paths of the changeset operations        #
##################################################


def test_changeset_update_on_closed_changeset(auth_api, add_response):
    add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    add_response(PUT, "/changeset/1414", status=409)

    auth_api.changeset_create()

    with pytest.raises(osmapi.ChangesetClosedApiError) as execinfo:
        auth_api.changeset_update({"test": "foobar"})

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload_str
        == "The changeset 1414 was closed at 2024-03-01 10:00:00 UTC."
    )


def test_changeset_update_server_error(auth_api, add_response):
    """A non-409 error is re-raised unchanged rather than mapped."""
    add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    # a 5xx is retried, so every attempt needs a registered response
    for _ in range(osmapi.http.OsmApiSession.MAX_RETRY_LIMIT):
        add_response(PUT, "/changeset/1414", status=500)

    auth_api.changeset_create()

    with pytest.raises(osmapi.ApiError) as execinfo:
        auth_api.changeset_update({"test": "foobar"})

    assert type(execinfo.value) is osmapi.ApiError
    assert execinfo.value.status == 500


def test_changeset_close_on_closed_changeset(auth_api, add_response):
    add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    add_response(PUT, "/changeset/1414/close", status=409)

    auth_api.changeset_create()

    with pytest.raises(osmapi.ChangesetClosedApiError) as execinfo:
        auth_api.changeset_close()

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload_str
        == "The changeset 1414 was closed at 2024-03-01 10:00:00 UTC."
    )


def test_changeset_comment_on_closed_changeset(auth_api, add_response):
    add_response(POST, "/changeset/123/comment", status=409)

    with pytest.raises(osmapi.ChangesetClosedApiError) as execinfo:
        auth_api.changeset_comment(123, comment="too late")

    assert execinfo.value.status == 409
    assert (
        execinfo.value.payload_str
        == "The changeset 123 was closed at 2024-03-01 10:00:00 UTC."
    )


def test_changeset_comment_not_found(auth_api, add_response):
    """A non-409 error is re-raised unchanged rather than mapped."""
    add_response(POST, "/changeset/123/comment", status=404)

    with pytest.raises(osmapi.ElementNotFoundApiError) as execinfo:
        auth_api.changeset_comment(123, comment="test comment")

    assert execinfo.value.status == 404


def test_changeset_subscribe_other_error(auth_api, add_response):
    """Only a 409 means 'already subscribed'; anything else is re-raised."""
    add_response(POST, "/changeset/52924/subscribe", status=403)

    with pytest.raises(osmapi.ApiError) as execinfo:
        auth_api.changeset_subscribe(52924)

    assert type(execinfo.value) is osmapi.ApiError
    assert execinfo.value.status == 403


def test_changeset_unsubscribe_other_error(auth_api, add_response):
    """Only a 404 means 'not subscribed'; anything else is re-raised."""
    add_response(POST, "/changeset/52924/unsubscribe", status=403)

    with pytest.raises(osmapi.ApiError) as execinfo:
        auth_api.changeset_unsubscribe(52924)

    assert type(execinfo.value) is osmapi.ApiError
    assert execinfo.value.status == 403


##################################################
# The changeset() context manager                #
##################################################


def test_changeset_contextmanager_closes_on_exception(auth_api, add_response):
    """An error inside the block must not leave the changeset open."""
    resp = add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    add_response(PUT, "/changeset/1414/close", filename="test_changeset_close.xml")

    with pytest.raises(ValueError, match="boom"):
        with auth_api.changeset({"comment": "will fail"}):
            raise ValueError("boom")

    assert "/api/0.6/changeset/1414/close" in resp.calls[1].request.url
    assert auth_api._current_changeset_id == 0


def test_changeset_contextmanager_reusable_after_exception(auth_api, add_response):
    """After a failed block a new changeset can be opened straight away."""
    add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    add_response(PUT, "/changeset/1414/close", filename="test_changeset_close.xml")
    add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    add_response(PUT, "/changeset/1414/close", filename="test_changeset_close.xml")

    with pytest.raises(ValueError):
        with auth_api.changeset():
            raise ValueError("boom")

    # would raise ChangesetAlreadyOpenError if the first one had leaked
    with auth_api.changeset() as changeset_id:
        assert changeset_id == 1414

    assert auth_api._current_changeset_id == 0


def test_changeset_get_include_discussion_without_discussion(api, add_response):
    """Asking for the discussion of a changeset that has none yields nothing."""
    resp = add_response(
        GET, "/changeset/52924", filename="test_changeset_get_without_discussion.xml"
    )

    result = api.changeset_get(52924, include_discussion=True)

    assert resp.calls[0].request.params == {"include_discussion": "true"}
    # the key is present but empty, rather than the parse failing
    assert result["discussion"] == []
    assert result["id"] == 52924


def test_changeset_update_without_tags(auth_api, add_response):
    """Called with no tags, only `created_by` is sent."""
    add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    resp = add_response(PUT, "/changeset/1414", filename="test_changeset_update.xml")

    auth_api.changeset_create()
    auth_api.changeset_update()

    assert xmltosorteddict(resp.calls[1].request.body) == xmltosorteddict(
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<osm version="0.6" generator="{GENERATOR}">'
        '<changeset visible="true">'
        f'<tag k="created_by" v="{GENERATOR}"/>'
        "</changeset>"
        "</osm>"
    )


def test_changeset_close_server_error(auth_api, add_response):
    """A non-409 error while closing is re-raised unchanged."""
    add_response(PUT, "/changeset/create", filename="test_changeset_create.xml")
    for _ in range(osmapi.http.OsmApiSession.MAX_RETRY_LIMIT):
        add_response(PUT, "/changeset/1414/close", status=500)

    auth_api.changeset_create()

    with pytest.raises(osmapi.ApiError) as execinfo:
        auth_api.changeset_close()

    assert type(execinfo.value) is osmapi.ApiError
    assert execinfo.value.status == 500
    # the changeset is still considered open, since closing it failed
    assert auth_api._current_changeset_id == 1414
