"""Tests for the error hierarchy."""

import warnings

import osmapi
import pytest


def test_payload_str_decodes_bytes():
    error = osmapi.ApiError(409, "Conflict", b"The changeset was closed")

    assert error.payload_str == "The changeset was closed"


def test_payload_str_passes_through_text():
    error = osmapi.ApiError(409, "Conflict", "already a string")

    assert error.payload_str == "already a string"


def test_payload_str_replaces_undecodable_bytes():
    error = osmapi.ApiError(500, "Server Error", b"caf\xff")

    assert error.payload_str == "caf�"


def test_payload_str_of_empty_payload():
    error = osmapi.ApiError(0, "Connection error", "")

    assert error.payload_str == ""


def test_api_error_str():
    error = osmapi.ApiError(404, "Not Found", b"no such element")

    assert str(error) == "Request failed: 404 - Not Found - b'no such element'"


@pytest.mark.parametrize(
    "error_class",
    [
        osmapi.UnauthorizedApiError,
        osmapi.ElementNotFoundApiError,
        osmapi.ElementDeletedApiError,
        osmapi.ChangesetClosedApiError,
        osmapi.VersionMismatchApiError,
        osmapi.PreconditionFailedApiError,
        osmapi.NoteAlreadyClosedApiError,
        osmapi.AlreadySubscribedApiError,
        osmapi.NotSubscribedApiError,
        osmapi.TimeoutApiError,
        osmapi.ConnectionApiError,
        osmapi.ResponseEmptyApiError,
        osmapi.RetriableApiError,
        osmapi.ServerApiError,
        osmapi.InternalServerApiError,
        osmapi.BadGatewayApiError,
        osmapi.ServiceUnavailableApiError,
        osmapi.GatewayTimeoutApiError,
        osmapi.RateLimitApiError,
    ],
)
def test_api_errors_are_catchable_as_api_error(error_class):
    """Every typed API error can be caught as ApiError and as OsmApiError."""
    error = error_class(500, "reason", b"payload")

    assert isinstance(error, osmapi.ApiError)
    assert isinstance(error, osmapi.OsmApiError)
    assert error.payload_str == "payload"


##################################################
# Retriable errors (server failures, rate limits)#
##################################################


@pytest.mark.parametrize(
    "error_class",
    [
        osmapi.ServerApiError,
        osmapi.InternalServerApiError,
        osmapi.BadGatewayApiError,
        osmapi.ServiceUnavailableApiError,
        osmapi.GatewayTimeoutApiError,
        osmapi.RateLimitApiError,
        osmapi.TimeoutApiError,
        osmapi.ConnectionApiError,
    ],
)
def test_transient_errors_are_catchable_as_retriable(error_class):
    """One `except` clause covers every failure that is worth trying again."""
    error = error_class(503, "Service Unavailable", b"try later")

    assert isinstance(error, osmapi.RetriableApiError)


@pytest.mark.parametrize(
    "error_class",
    [
        osmapi.InternalServerApiError,
        osmapi.BadGatewayApiError,
        osmapi.ServiceUnavailableApiError,
        osmapi.GatewayTimeoutApiError,
    ],
)
def test_server_errors_are_catchable_as_server_error(error_class):
    error = error_class(500, "Internal Server Error", b"boom")

    assert isinstance(error, osmapi.ServerApiError)


def test_rate_limit_error_is_not_a_server_error():
    """A quota is not a failure of the API, even though HTTP 509 is a 5xx."""
    error = osmapi.RateLimitApiError(509, "Bandwidth Limit Exceeded", b"too much")

    assert not isinstance(error, osmapi.ServerApiError)
    assert isinstance(error, osmapi.RetriableApiError)


def test_errors_that_are_not_retriable():
    """A request the API rejected is not retried, retrying would fail again."""
    for error_class in (
        osmapi.UnauthorizedApiError,
        osmapi.ElementNotFoundApiError,
        osmapi.ElementDeletedApiError,
        osmapi.VersionMismatchApiError,
        osmapi.PreconditionFailedApiError,
    ):
        assert not isinstance(
            error_class(400, "reason", b"payload"), osmapi.RetriableApiError
        )


def test_retry_after_defaults_to_none():
    error = osmapi.ApiError(500, "Internal Server Error", b"boom")

    assert error.retry_after is None


def test_retry_after_is_kept():
    error = osmapi.RateLimitApiError(429, "Too Many Requests", b"slow down", 120)

    assert error.retry_after == 120


##################################################
# Deprecated error names (to be removed in 7.0)  #
##################################################


@pytest.mark.parametrize(
    "module", [osmapi, osmapi.errors], ids=["osmapi", "osmapi.errors"]
)
def test_deprecated_error_name_resolves_to_new_class(module):
    """The old name is the new class, so existing `except` clauses still work."""
    with pytest.deprecated_call(match="renamed to AuthenticationMissingError"):
        error_class = module.UsernamePasswordMissingError

    assert error_class is osmapi.AuthenticationMissingError


def test_deprecated_error_name_catches_new_error():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        with pytest.raises(osmapi.UsernamePasswordMissingError):
            raise osmapi.AuthenticationMissingError("no credentials")


def test_deprecated_error_name_from_import_warns():
    with pytest.deprecated_call(match="removed in osmapi 7.0"):
        from osmapi.errors import UsernamePasswordMissingError

    assert UsernamePasswordMissingError is osmapi.AuthenticationMissingError


@pytest.mark.parametrize(
    "module", [osmapi, osmapi.errors], ids=["osmapi", "osmapi.errors"]
)
def test_unknown_attribute_still_raises_attribute_error(module):
    """The deprecation hook must not swallow typos."""
    with pytest.raises(AttributeError, match="NoSuchError"):
        module.NoSuchError
