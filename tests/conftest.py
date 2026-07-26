import osmapi
import pytest
from unittest import mock
import responses
import os
import re
import xmltodict

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

API_BASE = "http://api06.dev.openstreetmap.org"
PROD_API_BASE = "https://www.openstreetmap.org"

# The default `created_by` / generator string, which tracks the package version
GENERATOR = f"osmapi/{osmapi.__version__}"

# Changeset id used by tests that need an already-open changeset
OPEN_CHANGESET_ID = 1111


@pytest.fixture
def file_content():
    def _file_content(filename):
        path = os.path.join(__location__, "fixtures", filename)
        if not os.path.exists(path):
            return ""
        with open(path) as f:
            return f.read()

    return _file_content


@pytest.fixture
def api():
    api = osmapi.OsmApi(api=API_BASE)
    api._session._sleep = mock.Mock()

    yield api
    api.close()


@pytest.fixture
def auth_api():
    api = osmapi.OsmApi(api=API_BASE, username="testuser", password="testpassword")
    api._session._sleep = mock.Mock()

    yield api
    api.close()


@pytest.fixture
def changeset_api(auth_api):
    """An authenticated api with changeset `OPEN_CHANGESET_ID` already open.

    Element writes require an open changeset; this skips the changeset/create
    round-trip for tests that are about the element operation itself.
    """
    auth_api._current_changeset_id = OPEN_CHANGESET_ID
    return auth_api


@pytest.fixture
def prod_api():
    api = osmapi.OsmApi(api=PROD_API_BASE, username="testuser", password="testpassword")
    api._session._sleep = mock.Mock()

    yield api
    api.close()


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def add_response(mocked_responses, file_content, request):
    """Register a mocked response.

    `path` is relative to `/api/0.6`; use `url` for endpoints outside of it
    (e.g. `/api/capabilities`) or on another host. With neither, any URL on the
    dev API host matches — prefer naming one so the request URL is asserted too.
    """

    def _add_response(
        method, path=None, filename=None, body=None, status=200, url=None
    ):
        if not filename:
            # use testname by default
            filename = f"{request.node.originalname}.xml"

        if url is None:
            if path:
                url = f"{API_BASE}/api/0.6{path}"
            else:
                url = re.compile(r"http:\/\/api06\.dev\.openstreetmap\.org.*")

        if body is None:
            body = file_content(filename)
        mocked_responses.add(method, url=url, body=body, status=status)
        return mocked_responses

    return _add_response


@pytest.fixture
def xml_dict():
    """Parse an XML document into a dict, for whitespace-insensitive comparison."""

    def _xml_dict(xml):
        return xmltodict.parse(xml, dict_constructor=dict)

    return _xml_dict


@pytest.fixture
def assert_request_xml(xml_dict):
    """Assert that a request body carries the expected `<osm>` payload.

    `payload` is just the inner XML — the prolog and the `<osm>` envelope
    (with the generator string for the running version) are added here so
    tests don't have to repeat them or track the version number.
    """

    def _assert_request_xml(request, payload):
        expected = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<osm version="0.6" generator="{GENERATOR}">'
            f"{payload}"
            "</osm>"
        )
        assert xml_dict(request.body) == xml_dict(expected)

    return _assert_request_xml


def make_http_response(status=200, content="test response", reason="test reason"):
    """Build a minimal stand-in for a `requests` response."""
    response = mock.Mock()
    response.status_code = status
    response.reason = reason
    response.content = content
    return response


@pytest.fixture
def http_response():
    """Factory for fake `requests` responses, for use with `mock_api`."""
    return make_http_response


@pytest.fixture
def mock_api():
    """Factory for an OsmApi backed by a `unittest.mock` HTTP session.

    Unlike the `responses`-based fixtures this does not match on URL, so it is
    only for tests about the HTTP layer itself (status-code mapping, retries)
    where the response sequence matters more than the request. Returns a
    `(api, session_mock)` tuple.

    Pass `responses=[...]` to return a different response per attempt, or
    `side_effect=...` to raise.
    """
    created = []

    def _mock_api(
        status=200,
        content="test response",
        reason="test reason",
        auth=True,
        responses=None,
        side_effect=None,
    ):
        session = mock.Mock()
        session.close = mock.Mock()
        session.auth = ("testuser", "testpassword") if auth else None

        if side_effect is not None:
            session.request = mock.Mock(side_effect=side_effect)
        elif responses is not None:
            session.request = mock.Mock(side_effect=list(responses))
        else:
            session.request = mock.Mock(
                return_value=make_http_response(status, content, reason)
            )

        credentials = (
            {"username": "testuser", "password": "testpassword"} if auth else {}
        )
        api = osmapi.OsmApi(api=API_BASE, session=session, **credentials)
        api._session._sleep = mock.Mock()
        created.append(api)
        return api, session

    yield _mock_api
    for api in created:
        api.close()
