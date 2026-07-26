"""Tests for the error hierarchy."""

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
    ],
)
def test_api_errors_are_catchable_as_api_error(error_class):
    """Every typed API error can be caught as ApiError and as OsmApiError."""
    error = error_class(500, "reason", b"payload")

    assert isinstance(error, osmapi.ApiError)
    assert isinstance(error, osmapi.OsmApiError)
    assert error.payload_str == "payload"
