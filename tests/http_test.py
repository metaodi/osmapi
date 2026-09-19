"""Tests for the HTTP layer: status-code mapping and the retry loop."""

import datetime
from email.utils import format_datetime
from unittest import mock

import osmapi
import pytest
import requests

from .conftest import API_BASE, make_http_response


def test_http_request_get(mock_api):
    api, session = mock_api()

    response = api._session._http_request("GET", "/api/0.6/test", False, None)

    session.request.assert_called_with(
        "GET", f"{API_BASE}/api/0.6/test", data=None, timeout=30, params=None
    )
    assert response == "test response"
    assert session.request.call_count == 1


def test_http_request_put(mock_api):
    api, session = mock_api()

    response = api._session._http_request("PUT", "/api/0.6/testput", False, "data")

    session.request.assert_called_with(
        "PUT", f"{API_BASE}/api/0.6/testput", data="data", timeout=30, params=None
    )
    assert response == "test response"


def test_http_request_delete(mock_api):
    api, session = mock_api()

    response = api._session._http_request(
        "DELETE", "/api/0.6/testdelete", False, "delete data"
    )

    session.request.assert_called_with(
        "DELETE",
        f"{API_BASE}/api/0.6/testdelete",
        data="delete data",
        timeout=30,
        params=None,
    )
    assert response == "test response"


def test_http_request_auth(mock_api):
    api, session = mock_api()

    response = api._session._http_request("PUT", "/api/0.6/testauth", True, None)

    session.request.assert_called_with(
        "PUT", f"{API_BASE}/api/0.6/testauth", data=None, timeout=30, params=None
    )
    assert session.auth == ("testuser", "testpassword")
    assert response == "test response"


def test_http_request_auth_without_session(unauthenticated_api):
    """Without a session there is no way to authenticate, so osmapi refuses."""
    api, session = unauthenticated_api

    with pytest.raises(
        osmapi.AuthenticationMissingError, match="no session was provided"
    ):
        api._session._http_request("PUT", "/api/0.6/testauth", True, None)

    # the request is never attempted
    assert session.request.call_count == 0


def test_http_request_auth_with_session_without_credentials(mock_api):
    """A session is never second-guessed: the request is sent, the API decides.

    `session.auth` is not a reliable signal — requests-oauthlib sets it to a
    no-op lambda and adds the token per request, others only set an
    `Authorization` header — so a session without visible credentials is
    still sent, and a real authorization problem comes back as a 401.
    """
    api, session = mock_api(auth=False)

    response = api._session._http_request("PUT", "/api/0.6/testauth", True, None)

    assert session.request.call_count == 1
    assert response == "test response"


def test_http_request_auth_with_authorization_header():
    """The setup OSM actually uses: a bearer token, no `session.auth` at all."""
    session = requests.Session()
    session.headers["Authorization"] = "Bearer test-token"
    session.request = mock.Mock(return_value=make_http_response())
    api = osmapi.OsmApi(api=API_BASE, session=session)

    response = api._session._http_request("PUT", "/api/0.6/testauth", True, None)

    assert session.request.call_count == 1
    assert response == "test response"
    api.close()


@pytest.mark.parametrize(
    "status,expected",
    [
        (401, osmapi.UnauthorizedApiError),
        (404, osmapi.ElementNotFoundApiError),
        (410, osmapi.ElementDeletedApiError),
        (429, osmapi.RateLimitApiError),
        (500, osmapi.InternalServerApiError),
        (502, osmapi.BadGatewayApiError),
        (503, osmapi.ServiceUnavailableApiError),
        (504, osmapi.GatewayTimeoutApiError),
        (509, osmapi.RateLimitApiError),
    ],
)
def test_http_request_error_status_mapping(mock_api, status, expected):
    api, _ = mock_api(status=status)

    with pytest.raises(expected) as execinfo:
        api._session._http_request("GET", f"/api/0.6/test{status}", False, None)

    assert type(execinfo.value) is expected
    assert execinfo.value.status == status
    assert execinfo.value.reason == "test reason"
    assert execinfo.value.payload == "test response"


def test_http_request_unmapped_server_error(mock_api):
    """Any other 5xx is still recognisable as a failure on the OSM side."""
    api, _ = mock_api(status=507)

    with pytest.raises(osmapi.ServerApiError) as execinfo:
        api._session._http_request("GET", "/api/0.6/test", False, None)

    assert type(execinfo.value) is osmapi.ServerApiError
    assert execinfo.value.status == 507


def test_http_request_unmapped_client_error(mock_api):
    """A 4xx without its own class stays a plain, non-retriable ApiError."""
    api, _ = mock_api(status=405)

    with pytest.raises(osmapi.ApiError) as execinfo:
        api._session._http_request("GET", "/api/0.6/test", False, None)

    assert type(execinfo.value) is osmapi.ApiError
    assert not isinstance(execinfo.value, osmapi.RetriableApiError)


##################################################
# The Retry-After header                         #
##################################################


def test_http_request_retry_after_seconds(mock_api):
    api, _ = mock_api(status=429, headers={"Retry-After": "120"})

    with pytest.raises(osmapi.RateLimitApiError) as execinfo:
        api._session._http_request("GET", "/api/0.6/test", False, None)

    assert execinfo.value.retry_after == 120


def test_http_request_retry_after_http_date(mock_api):
    """The other form RFC 9110 allows: an absolute date instead of a delay."""
    retry_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        seconds=90
    )
    api, _ = mock_api(
        status=503, headers={"Retry-After": format_datetime(retry_at, usegmt=True)}
    )

    with pytest.raises(osmapi.ServiceUnavailableApiError) as execinfo:
        api._session._http_request("GET", "/api/0.6/test", False, None)

    # the header has a resolution of one second, so allow for the rounding
    assert 88 <= execinfo.value.retry_after <= 90


def test_http_request_retry_after_in_the_past(mock_api):
    """A date that has already passed means "retry now", not a negative wait."""
    retry_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        seconds=90
    )
    api, _ = mock_api(
        status=503, headers={"Retry-After": format_datetime(retry_at, usegmt=True)}
    )

    with pytest.raises(osmapi.ServiceUnavailableApiError) as execinfo:
        api._session._http_request("GET", "/api/0.6/test", False, None)

    assert execinfo.value.retry_after == 0


@pytest.mark.parametrize(
    "header",
    [
        {},
        {"Retry-After": "later please"},
        # float() would accept these, and time.sleep() would then fail
        {"Retry-After": "inf"},
        {"Retry-After": "nan"},
    ],
)
def test_http_request_without_usable_retry_after(mock_api, header):
    api, _ = mock_api(status=503, headers=header)

    with pytest.raises(osmapi.ServiceUnavailableApiError) as execinfo:
        api._session._http_request("GET", "/api/0.6/test", False, None)

    assert execinfo.value.retry_after is None


def test_http_request_empty_response(mock_api):
    api, _ = mock_api(content="")

    with pytest.raises(osmapi.ResponseEmptyApiError):
        api._session._http_request("GET", "/api/0.6/test", False, None)


def test_http_request_empty_response_allowed(mock_api):
    """With `return_value=False` an empty body is not an error."""
    api, _ = mock_api(content="")

    result = api._session._http_request(
        "PUT", "/api/0.6/test", False, None, return_value=False
    )

    assert result == ""


def test_http_request_timeout(mock_api):
    api, _ = mock_api(side_effect=requests.exceptions.Timeout())

    with pytest.raises(osmapi.TimeoutApiError) as execinfo:
        api._session._http_request("GET", "/api/0.6/test", False, None)

    assert execinfo.value.status == 0
    assert "Request timed out (timeout=30)" in execinfo.value.reason


def test_http_request_connection_error(mock_api):
    api, _ = mock_api(side_effect=requests.exceptions.ConnectionError("boom"))

    with pytest.raises(osmapi.ConnectionApiError) as execinfo:
        api._session._http_request("GET", "/api/0.6/test", False, None)

    assert execinfo.value.status == 0
    assert "Connection error: boom" in execinfo.value.reason


def test_http_request_generic_request_exception(mock_api):
    """Any other `requests` error becomes a plain ApiError with status 0."""
    api, _ = mock_api(side_effect=requests.exceptions.RequestException("nope"))

    with pytest.raises(osmapi.ApiError) as execinfo:
        api._session._http_request("GET", "/api/0.6/test", False, None)

    assert execinfo.value.status == 0
    assert execinfo.value.reason == "nope"


##################################################
# Retry behaviour of _http()                     #
##################################################


def test_http_retries_server_error_then_succeeds(mock_api):
    api, session = mock_api(
        responses=[
            make_http_response(status=500),
            make_http_response(status=502),
            make_http_response(status=200, content="ok"),
        ]
    )

    result = api._session._http("GET", "/api/0.6/test", False, None)

    assert result == "ok"
    assert session.request.call_count == 3
    # the first retry is immediate, only later ones wait
    assert api._session._sleep.call_count == 1


def test_http_gives_up_after_max_retries_on_server_error(mock_api):
    api, session = mock_api(status=500)

    with pytest.raises(osmapi.ApiError) as execinfo:
        api._session._http("GET", "/api/0.6/test", False, None)

    assert execinfo.value.status == 500
    assert session.request.call_count == api._session.MAX_RETRY_LIMIT
    assert api._session._sleep.call_count == api._session.MAX_RETRY_LIMIT - 2


def test_http_does_not_retry_client_error(mock_api):
    api, session = mock_api(status=404)

    with pytest.raises(osmapi.ElementNotFoundApiError):
        api._session._http("GET", "/api/0.6/test", False, None)

    assert session.request.call_count == 1
    assert api._session._sleep.call_count == 0


def test_http_waits_longer_after_every_attempt(mock_api):
    """Retrying an overloaded server immediately only adds to the load."""
    api, session = mock_api(status=500)

    with pytest.raises(osmapi.InternalServerApiError):
        api._session._http("GET", "/api/0.6/test", False, None)

    assert session.request.call_count == 5
    # the first retry is immediate, the waits then double
    assert api._session._sleep.call_args_list == [
        mock.call(5),
        mock.call(10),
        mock.call(20),
    ]


def test_http_retries_rate_limit(mock_api):
    """A rate limit used to raise right away, now it is waited out."""
    api, session = mock_api(
        responses=[
            make_http_response(status=429, headers={"Retry-After": "30"}),
            make_http_response(status=200, content="ok"),
        ]
    )

    result = api._session._http("GET", "/api/0.6/test", False, None)

    assert result == "ok"
    assert session.request.call_count == 2
    # even the first retry waits when the API asked us to
    api._session._sleep.assert_called_once_with(30)


def test_http_gives_up_after_max_retries_on_rate_limit(mock_api):
    api, session = mock_api(status=429)

    with pytest.raises(osmapi.RateLimitApiError) as execinfo:
        api._session._http("GET", "/api/0.6/test", False, None)

    assert execinfo.value.status == 429
    assert session.request.call_count == api._session.MAX_RETRY_LIMIT


def test_http_caps_the_requested_delay(mock_api):
    """A break of an hour is the caller's decision to make, not ours."""
    api, _ = mock_api(status=503, headers={"Retry-After": "3600"})

    with pytest.raises(osmapi.ServiceUnavailableApiError) as execinfo:
        api._session._http("GET", "/api/0.6/test", False, None)

    assert api._session._sleep.call_args_list == [mock.call(60)] * 4
    # the caller can still wait out the full delay the API asked for
    assert execinfo.value.retry_after == 3600


@pytest.mark.parametrize(
    "error",
    [requests.exceptions.Timeout(), requests.exceptions.ConnectionError("boom")],
    ids=["timeout", "connection"],
)
def test_http_does_not_retry_unreachable_server(mock_api, error):
    """Retrying a timeout would block for a multiple of the timeout itself."""
    api, session = mock_api(side_effect=error)

    with pytest.raises(osmapi.RetriableApiError):
        api._session._http("GET", "/api/0.6/test", False, None)

    assert session.request.call_count == 1
    assert api._session._sleep.call_count == 0


def test_http_does_not_retry_missing_authentication(unauthenticated_api):
    api, session = unauthenticated_api

    with pytest.raises(osmapi.AuthenticationMissingError):
        api._session._http("PUT", "/api/0.6/test", True, None)

    assert session.request.call_count == 0
    assert api._session._sleep.call_count == 0


def test_http_retries_unexpected_exception(mock_api):
    api, session = mock_api(side_effect=ValueError("kaboom"))

    with pytest.raises(
        osmapi.MaximumRetryLimitReachedError, match="Give up after 5 retries"
    ):
        api._session._http("GET", "/api/0.6/test", False, None)

    assert session.request.call_count == api._session.MAX_RETRY_LIMIT
    assert api._session._sleep.call_count == api._session.MAX_RETRY_LIMIT - 2


def test_http_reraises_osm_api_error_after_max_retries(mock_api):
    """An OsmApiError is re-raised as-is rather than wrapped."""
    api, session = mock_api(side_effect=osmapi.XmlResponseInvalidError("bad xml"))

    with pytest.raises(osmapi.XmlResponseInvalidError, match="bad xml"):
        api._session._http("GET", "/api/0.6/test", False, None)

    assert session.request.call_count == api._session.MAX_RETRY_LIMIT


def test_http_recreates_session_between_retries(mock_api):
    api, session = mock_api(
        responses=[make_http_response(status=500), make_http_response(content="ok")]
    )
    headers_updates_before = session.headers.update.call_count

    api._session._http("GET", "/api/0.6/test", False, None)

    # _get_http_session() re-applies auth and the user-agent on every rebuild
    assert session.headers.update.call_count == headers_updates_before + 1


def test_sleep_waits_five_seconds():
    session = osmapi.http.OsmApiSession(API_BASE, "osmapi/test")

    with mock.patch("osmapi.http.time.sleep") as sleep:
        session._sleep()

    sleep.assert_called_once_with(5)
    session.close()
