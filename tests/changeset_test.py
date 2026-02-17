import osmapi
import xmltodict
import datetime
import pytest
from responses import GET, PUT, POST
import requests


def xmltosorteddict(xml):
    xml_dict = xmltodict.parse(xml, dict_constructor=dict)
    return xml_dict


def test_Changeset_contextmanager(auth_api, add_response):
    # Setup mock
    resp = add_response(PUT, "/changeset/create", filename="test_Changeset_create.xml")
    resp = add_response(PUT, "/node/create", filename="test_Changeset_create_node.xml")
    resp = add_response(
        PUT, "/changeset/1414/close", filename="test_Changeset_close.xml"
    )

    test_node = {
        "lat": 47.123,
        "lon": 8.555,
        "tag": {"amenity": "place_of_worship", "religion": "pastafarian"},
    }

    # use context manager
    with auth_api.Changeset() as changeset_id:
        assert changeset_id == 1414

        # add test node
        node = auth_api.NodeCreate(test_node)
        assert node["id"] == 7272

    # check requests
    assert len(resp.calls) == 3


def test_ChangesetGet(api, add_response):
    # Setup mock
    add_response(GET, "/changeset/123")

    # Call
    result = api.ChangesetGet(123)

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


def test_ChangesetGet_with_connection_error(api, add_response):
    # Setup mock
    add_response(
        GET,
        "/changeset/123",
        body=requests.exceptions.ConnectionError("Connection aborted."),
    ),

    # Call
    with pytest.raises(osmapi.ConnectionApiError) as execinfo:
        api.ChangesetGet(123)
    assert (
        str(execinfo.value)
        == "Request failed: 0 - Connection error: Connection aborted. - "
    )


def test_ChangesetGet_with_timeout(api, add_response):
    # Setup mock
    add_response(GET, "/changeset/123", body=requests.exceptions.Timeout())

    # Call
    with pytest.raises(osmapi.TimeoutApiError) as execinfo:
        api.ChangesetGet(123)
    assert (
        str(execinfo.value) == "Request failed: 0 - Request timed out (timeout=30) - "
    )


def test_ChangesetUpdate(auth_api, add_response):
    # Setup mock
    resp = add_response(PUT, "/changeset/create", filename="test_ChangesetCreate.xml")
    resp = add_response(PUT, "/changeset/4321", filename="test_ChangesetUpdate.xml")

    # Call
    result = auth_api.ChangesetCreate()
    assert result == 4321

    result = auth_api.ChangesetUpdate({"test": "foobar"})
    changeset_xml = xmltosorteddict(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<osm version="0.6" generator="osmapi/4.3.0">\n'
        b'  <changeset visible="true">\n'
        b'    <tag k="test" v="foobar"/>\n'
        b'    <tag k="created_by" v="osmapi/4.3.0"/>\n'
        b"  </changeset>\n"
        b"</osm>\n"
    )
    assert xmltosorteddict(resp.calls[1].request.body) == changeset_xml
    assert result == 4321


def test_ChangesetUpdate_with_created_by(auth_api, add_response):
    # Setup mock
    resp = add_response(PUT, "/changeset/create", filename="test_ChangesetCreate.xml")
    resp = add_response(PUT, "/changeset/4321", filename="test_ChangesetUpdate.xml")

    # Call
    result = auth_api.ChangesetCreate()
    assert result == 4321

    result = auth_api.ChangesetUpdate({"test": "foobar", "created_by": "MyTestOSMApp"})
    changeset_xml = xmltosorteddict(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<osm version="0.6" generator="osmapi/4.3.0">\n'
        b'  <changeset visible="true">\n'
        b'    <tag k="test" v="foobar"/>\n'
        b'    <tag k="created_by" v="MyTestOSMApp"/>\n'
        b"  </changeset>\n"
        b"</osm>\n"
    )
    assert xmltosorteddict(resp.calls[1].request.body) == changeset_xml
    assert result == 4321


def test_ChangesetUpdate_wo_changeset(auth_api):
    with pytest.raises(osmapi.NoChangesetOpenError) as execinfo:
        auth_api.ChangesetUpdate({"test": "foobar"})
    assert str(execinfo.value) == "No changeset currently opened"


def test_ChangesetCreate(auth_api, add_response):
    resp = add_response(PUT, "/changeset/create")
    result = auth_api.ChangesetCreate({"foobar": "A new test changeset"})
    assert result == 4321

    changeset_xml = xmltosorteddict(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<osm version="0.6" generator="osmapi/4.3.0">\n'
        b'  <changeset visible="true">\n'
        b'    <tag k="foobar" v="A new test changeset"/>\n'
        b'    <tag k="created_by" v="osmapi/4.3.0"/>\n'
        b"  </changeset>\n"
        b"</osm>\n"
    )
    assert xmltosorteddict(resp.calls[0].request.body) == changeset_xml


def test_ChangesetCreate_with_created_by(auth_api, add_response):
    resp = add_response(PUT, "/changeset/create")

    result = auth_api.ChangesetCreate(
        {
            "foobar": "A new test changeset",
            "created_by": "CoolTestApp",
        }
    )
    assert result == 1234

    changeset_xml = xmltosorteddict(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<osm version="0.6" generator="osmapi/4.3.0">\n'
        b'  <changeset visible="true">\n'
        b'    <tag k="foobar" v="A new test changeset"/>\n'
        b'    <tag k="created_by" v="CoolTestApp"/>\n'
        b"  </changeset>\n"
        b"</osm>\n"
    )
    assert xmltosorteddict(resp.calls[0].request.body) == changeset_xml


def test_ChangesetCreate_with_open_changeset(auth_api, add_response):
    add_response(PUT, "/changeset/create")

    auth_api.ChangesetCreate(
        {
            "test": "an already open changeset",
        }
    )

    with pytest.raises(osmapi.ChangesetAlreadyOpenError) as execinfo:
        auth_api.ChangesetCreate({"test": "foobar"})
    assert str(execinfo.value) == "Changeset already opened"


def test_ChangesetCreate_with_prod_api_and_test_comment(prod_api):
    with pytest.raises(osmapi.OsmApiError) as execinfo:
        prod_api.ChangesetCreate(
            {
                "comment": "My first test",
            }
        )
    assert (
        str(execinfo.value) == "DO NOT CREATE test changesets on the production server"
    )


def test_ChangesetClose(auth_api, add_response):
    # setup mock
    resp = add_response(PUT, "/changeset/create", filename="test_Changeset_create.xml")
    resp = add_response(PUT, "/changeset/1414/close")

    # Call
    auth_api.ChangesetCreate()
    auth_api.ChangesetClose()

    assert "/api/0.6/changeset/1414/close" in resp.calls[1].request.url


def test_ChangesetClose_with_no_changeset(auth_api):
    with pytest.raises(osmapi.NoChangesetOpenError) as execinfo:
        auth_api.ChangesetClose()
    assert str(execinfo.value) == "No changeset currently opened"


def test_ChangesetUpload_create_node(auth_api, add_response):
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
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<osmChange version="0.6" generator="osmapi/4.3.0">\n'
        b"<create>\n"
        b'  <node lat="47.123" lon="8.555" visible="true" '
        b'changeset="4444">\n'
        b'    <tag k="amenity" v="place_of_worship"/>\n'
        b'    <tag k="religion" v="pastafarian"/>\n'
        b"  </node>\n"
        b'  <node lat="47.125" lon="8.557" visible="true" '
        b'changeset="4444">\n'
        b'    <tag k="amenity" v="place_of_worship"/>\n'
        b'    <tag k="religion" v="pastafarian"/>\n'
        b"  </node>\n"
        b"</create>\n"
        b"</osmChange>"
    )

    # Call
    auth_api.ChangesetCreate()
    result = auth_api.ChangesetUpload(changesdata)

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


def test_ChangesetUpload_modify_way(auth_api, add_response):
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
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<osmChange version="0.6" generator="osmapi/4.3.0">\n'
        b"<modify>\n"
        b'  <way id="4294967296" version="2" visible="true" '
        b'changeset="4444">\n'
        b'    <tag k="highway" v="secondary"/>\n'
        b'    <tag k="name" v="Stansted Road"/>\n'
        b'    <nd ref="4295832773"/>\n'
        b'    <nd ref="4295832773"/>\n'
        b'    <nd ref="4294967304"/>\n'
        b'    <nd ref="4294967303"/>\n'
        b'    <nd ref="4294967300"/>\n'
        b'    <nd ref="4608751"/>\n'
        b'    <nd ref="4294967305"/>\n'
        b'    <nd ref="4294967302"/>\n'
        b'    <nd ref="8548430"/>\n'
        b'    <nd ref="4294967296"/>\n'
        b'    <nd ref="4294967301"/>\n'
        b'    <nd ref="4294967298"/>\n'
        b'    <nd ref="4294967306"/>\n'
        b'    <nd ref="7855737"/>\n'
        b'    <nd ref="4294967297"/>\n'
        b'    <nd ref="4294967299"/>\n'
        b"  </way>\n"
        b"</modify>\n"
        b"</osmChange>"
    )

    # Call
    auth_api.ChangesetCreate()
    result = auth_api.ChangesetUpload(changesdata)
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


def test_ChangesetUpload_delete_relation(auth_api, add_response):
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
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<osmChange version="0.6" generator="osmapi/4.3.0">\n'
        b"<delete>\n"
        b'  <relation id="676" version="2" visible="true" '
        b'changeset="4444">\n'
        b'    <tag k="admin_level" v="9"/>\n'
        b'    <tag k="boundary" v="administrative"/>\n'
        b'    <tag k="type" v="multipolygon"/>\n'
        b'    <member type="way" ref="4799" role="outer"/>\n'
        b'    <member type="way" ref="9391" role="outer"/>\n'
        b"  </relation>\n"
        b"</delete>\n"
        b"</osmChange>"
    )

    # Call
    auth_api.ChangesetCreate()
    result = auth_api.ChangesetUpload(changesdata)

    # Assert
    assert xmltosorteddict(resp.calls[1].request.body) == upload_xml
    assert result[0]["type"] == changesdata[0]["type"]
    assert result[0]["action"] == changesdata[0]["action"]

    data = result[0]["data"][0]
    assert data["member"], changesdata[0]["data"][0]["member"]
    assert data["tag"] == changesdata[0]["data"][0]["tag"]
    assert data["id"] == 676
    assert "version" not in data


def test_ChangesetUpload_invalid_response(auth_api, add_response):
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
    auth_api.ChangesetCreate()
    with pytest.raises(osmapi.XmlResponseInvalidError) as execinfo:
        auth_api.ChangesetUpload(changesdata)
    assert "The XML response from the OSM API is invalid" in str(execinfo.value)


def test_ChangesetUpload_no_auth(api):
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

    with pytest.raises(osmapi.UsernamePasswordMissingError) as execinfo:
        api.ChangesetUpload(changesdata)
    assert str(execinfo.value) == "Username/Password missing"


def test_ChangesetDownload(api, add_response):
    # Setup mock
    add_response(GET, "/changeset/23123/download")

    # Call
    result = api.ChangesetDownload(23123)

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


def test_ChangesetDownload_invalid_response(api, add_response):
    add_response(GET, "/changeset/23123/download")
    with pytest.raises(osmapi.XmlResponseInvalidError) as execinfo:
        api.ChangesetDownload(23123)
    assert "The XML response from the OSM API is invalid" in str(execinfo.value)


def test_ChangesetDownloadContainingUnicode(api, add_response):
    add_response(GET, "/changeset/37393499/download")

    # This changeset contains unicode tag values
    # Note that the fixture data has been reduced from the
    # original from openstreetmap.org
    result = api.ChangesetDownload(37393499)

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


def test_ChangesetsGet(api, add_response):
    resp = add_response(GET, "/changesets")

    result = api.ChangesetsGet(only_closed=True, username="metaodi")

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


def test_ChangesetGetWithComment(api, add_response):
    resp = add_response(GET, "/changeset/52924")

    result = api.ChangesetGet(52924, include_discussion=True)

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


def test_ChangesetGetWithoutDiscussion(api, add_response):
    resp = add_response(GET, "/changeset/52924")

    result = api.ChangesetGet(52924, include_discussion=False)

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


def test_ChangesetComment(auth_api, add_response):
    resp = add_response(POST, "/changeset/123/comment")

    result = auth_api.ChangesetComment(123, comment="test comment")

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


def test_ChangesetComment_no_auth(api):
    with pytest.raises(osmapi.UsernamePasswordMissingError) as execinfo:
        api.ChangesetComment(123, comment="test comment")
    assert str(execinfo.value) == "Username/Password missing"


def test_ChangesetSubscribe(auth_api, add_response):
    add_response(POST, "/changeset/123/subscribe")

    result = auth_api.ChangesetSubscribe(123)

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


def test_ChangesetSubscribeWhenAlreadySubscribed(auth_api, add_response):
    add_response(POST, "/changeset/52924/subscribe", status=409)

    with pytest.raises(osmapi.AlreadySubscribedApiError) as execinfo:
        auth_api.ChangesetSubscribe(52924)

    assert execinfo.value.payload == b"You are already subscribed to changeset 52924."
    assert execinfo.value.reason == "Conflict"
    assert execinfo.value.status == 409


def test_ChangesetSubscribe_no_auth(api):
    with pytest.raises(osmapi.UsernamePasswordMissingError) as execinfo:
        api.ChangesetSubscribe(45627)
    assert str(execinfo.value) == "Username/Password missing"


def test_ChangesetUnsubscribe(auth_api, add_response):
    add_response(POST, "/changeset/123/unsubscribe")

    result = auth_api.ChangesetUnsubscribe(123)

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


def test_ChangesetUnsubscribeWhenNotSubscribed(auth_api, add_response):
    add_response(POST, "/changeset/52924/unsubscribe", status=404)

    with pytest.raises(osmapi.NotSubscribedApiError) as execinfo:
        auth_api.ChangesetUnsubscribe(52924)

    assert execinfo.value.payload == b"You are not subscribed to changeset 52924."
    assert execinfo.value.reason == "Not Found"
    assert execinfo.value.status == 404


def test_ChangesetUnsubscribe_no_auth(api):
    with pytest.raises(osmapi.UsernamePasswordMissingError) as execinfo:
        api.ChangesetUnsubscribe(45627)
    assert str(execinfo.value) == "Username/Password missing"
