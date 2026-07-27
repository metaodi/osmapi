"""Tests for construction and lifecycle of the OsmApi object."""

from unittest import mock

import osmapi
import pytest
import requests

from .conftest import API_BASE, authenticated_session


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


def test_constructor_without_session_cannot_authenticate():
    api = osmapi.OsmApi(api=API_BASE)

    assert api._session._auth is None
    assert api._session._can_authenticate is False
    api.close()


def test_constructor_takes_auth_from_session():
    """Authentication comes from the session, there is no other way to set it."""
    api = osmapi.OsmApi(api=API_BASE, session=authenticated_session())

    assert api._session._auth == ("testuser", "testpassword")
    assert api._session._can_authenticate is True
    api.close()


def test_constructor_trusts_a_session_without_visible_credentials():
    """A session may authenticate in ways osmapi cannot inspect."""
    api = osmapi.OsmApi(api=API_BASE, session=requests.Session())

    assert api._session._auth is None
    assert api._session._can_authenticate is True
    api.close()


@pytest.mark.parametrize("credential", ["username", "password", "passwordfile"])
def test_constructor_rejects_username_password(credential):
    """Username/password auth was removed in 6.0, an OAuth session is required."""
    with pytest.raises(TypeError):
        osmapi.OsmApi(api=API_BASE, **{credential: "testuser"})


def test_close_call(mock_api):
    api, session = mock_api()

    api.close()

    assert session.close.call_count == 1


def test_close_context_manager():
    with osmapi.OsmApi() as api:
        api._session.close = mock.Mock()

    assert api._session.close.call_count == 1
