import osmapi
import pytest
from unittest import mock
import responses
import os
import re

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


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
    api_base = "http://api06.dev.openstreetmap.org"
    api = osmapi.OsmApi(api=api_base)
    api._session._sleep = mock.Mock()

    yield api
    api.close()


@pytest.fixture
def auth_api():
    api_base = "http://api06.dev.openstreetmap.org"
    api = osmapi.OsmApi(api=api_base, username="testuser", password="testpassword")
    api._session._sleep = mock.Mock()

    yield api
    api.close()


@pytest.fixture
def prod_api():
    api_base = "https://www.openstreetmap.org"
    api = osmapi.OsmApi(api=api_base, username="testuser", password="testpassword")
    api._session._sleep = mock.Mock()

    yield api
    api.close()


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def add_response(mocked_responses, file_content, request):
    def _add_response(method, path=None, filename=None, body=None, status=200):
        if not filename:
            # use testname by default
            filename = f"{request.node.originalname}.xml"

        if path:
            url = f"http://api06.dev.openstreetmap.org/api/0.6{path}"
        else:
            url = re.compile(r"http:\/\/api06\.dev\.openstreetmap\.org.*")

        if not body:
            body = file_content(filename)
        mocked_responses.add(method, url=url, body=body, status=status)
        return mocked_responses

    return _add_response
