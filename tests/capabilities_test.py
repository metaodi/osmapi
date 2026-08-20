from responses import GET


def test_capabilities(api, add_response):
    resp = add_response(GET, url="http://api06.dev.openstreetmap.org/api/capabilities")

    result = api.capabilities()

    assert resp.calls[0].request.method == "GET"
    assert (
        resp.calls[0].request.url
        == "http://api06.dev.openstreetmap.org/api/capabilities"
    )
    assert result == {
        "area": {"maximum": 0.25},
        "changesets": {"maximum_elements": 50000.0},
        "status": {"api": "mocked", "database": "online", "gpx": "online"},
        "timeout": {"seconds": 300.0},
        "tracepoints": {"per_page": 5000.0},
        "version": {"maximum": 0.6, "minimum": 0.6},
        "waynodes": {"maximum": 2000.0},
    }


def test_map(api, add_response):
    resp = add_response(GET, "/map")

    result = api.map(8.765, 47.287, 8.767, 47.289)

    # the bbox is formatted with 6 decimal places
    assert resp.calls[0].request.url == (
        "http://api06.dev.openstreetmap.org/api/0.6/map"
        "?bbox=8.765000,47.287000,8.767000,47.289000"
    )

    assert [elem["type"] for elem in result] == ["node", "node", "way", "relation"]
    assert result[0]["data"]["id"] == 11949
    assert result[0]["data"]["lat"] == 47.2871
    assert result[1]["data"]["tag"] == {"amenity": "bench"}
    assert result[2]["data"]["nd"] == [11949, 11950]
    assert result[3]["data"]["member"] == [{"ref": 321, "role": "outer", "type": "way"}]


def test_map_iter(api, add_response):
    resp = add_response(GET, "/map", filename="test_map.xml")

    result = list(api.map_iter(8.765, 47.287, 8.767, 47.289))

    assert resp.calls[0].request.url == (
        "http://api06.dev.openstreetmap.org/api/0.6/map"
        "?bbox=8.765000,47.287000,8.767000,47.289000"
    )
    assert [elem["type"] for elem in result] == ["node", "node", "way", "relation"]
    assert result[0]["data"]["id"] == 11949
    assert result[2]["data"]["nd"] == [11949, 11950]
    assert result[3]["data"]["member"] == [{"ref": 321, "role": "outer", "type": "way"}]


def test_map_negative_bbox(api, add_response):
    resp = add_response(GET, "/map", filename="test_map.xml")

    api.map(-1.5, -45.9667901, -1.4831815, 52.4710193)

    assert resp.calls[0].request.url == (
        "http://api06.dev.openstreetmap.org/api/0.6/map"
        "?bbox=-1.500000,-45.966790,-1.483181,52.471019"
    )


def test_map_empty(api, add_response):
    add_response(GET, "/map")

    result = api.map(8.765, 47.287, 8.7651, 47.2871)

    assert result == []
