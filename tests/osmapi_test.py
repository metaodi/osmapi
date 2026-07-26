"""Tests for construction and lifecycle of the OsmApi object."""

import os
from unittest import mock

import osmapi

from .conftest import API_BASE

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def fixture_path(filename):
    return os.path.join(__location__, "fixtures", filename)


def test_constructor():
    api = osmapi.OsmApi(api=API_BASE)

    assert isinstance(api, osmapi.OsmApi)
    api.close()


def test_constructor_strips_trailing_slash():
    api = osmapi.OsmApi(api=f"{API_BASE}/")

    assert api._api == API_BASE
    api.close()


def test_constructor_created_by_defaults_to_version():
    api = osmapi.OsmApi(api=API_BASE)

    assert api._created_by == f"osmapi/{osmapi.__version__}"
    api.close()


def test_constructor_with_appid():
    """`appid` is prefixed to the generator / user-agent string."""
    api = osmapi.OsmApi(api=API_BASE, appid="MyApp/1.0")

    assert api._created_by == f"MyApp/1.0 (osmapi/{osmapi.__version__})"
    assert api._session._session.headers["user-agent"] == api._created_by
    api.close()


def test_constructor_with_custom_created_by():
    api = osmapi.OsmApi(api=API_BASE, created_by="custom/9.9")

    assert api._created_by == "custom/9.9"
    api.close()


def test_no_changeset_open_initially():
    api = osmapi.OsmApi(api=API_BASE)

    assert api._current_changeset_id == 0
    api.close()


def test_passwordfile_only():
    api = osmapi.OsmApi(passwordfile=fixture_path("passwordfile.txt"))

    assert api._username == "testosm"
    assert api._password == "testpass"
    api.close()


def test_passwordfile_with_user():
    api = osmapi.OsmApi(
        username="testuser", passwordfile=fixture_path("passwordfile.txt")
    )

    assert api._username == "testuser"
    assert api._password == "testuserpass"
    api.close()


def test_passwordfile_with_colon():
    api = osmapi.OsmApi(
        username="testuser", passwordfile=fixture_path("passwordfile_colon.txt")
    )

    assert api._username == "testuser"
    assert api._password == "test:userpass"
    api.close()


def test_close_call(mock_api):
    api, session = mock_api()

    api.close()

    assert session.close.call_count == 1


def test_close_context_manager():
    with osmapi.OsmApi() as api:
        api._session.close = mock.Mock()

    assert api._session.close.call_count == 1
