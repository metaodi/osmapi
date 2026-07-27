"""
Error classes for the OpenStreetMap API."""

import warnings
from typing import Any


class OsmApiError(Exception):
    """
    General OsmApi error class to provide a superclass for all other errors
    """


class MaximumRetryLimitReachedError(OsmApiError):
    """
    Error when the maximum amount of retries is reached and we have to give up
    """


class AuthenticationMissingError(OsmApiError):
    """
    Error when a request requires authentication, but no session was provided
    that could carry credentials.

    Pass an authenticated `requests.Session` (e.g. an OAuth 2.0 session, see
    the [README](https://github.com/metaodi/osmapi#oauth-authentication)) to
    `OsmApi` to make authenticated requests.

    This error is raised before the request is sent, and only when `OsmApi`
    created the http session itself — in that case there is no way for the
    request to be authenticated. A session that was passed in is never
    second-guessed (it can carry a token in `session.auth`, in an
    `Authorization` header, in a transport adapter, or add it per request),
    so a missing or invalid authorization on such a session is reported by
    the API as `OsmApi.UnauthorizedApiError` (HTTP 401) instead.

    Before version 6.0 this error was called `UsernamePasswordMissingError`.
    That name still works, but it is deprecated and will be removed in
    version 7.0.
    """

    pass


class NoChangesetOpenError(OsmApiError):
    """
    Error when an operation requires an open changeset, but currently
    no changeset _is_ open
    """

    pass


class ChangesetAlreadyOpenError(OsmApiError):
    """
    Error when a user tries to open a changeset when there is already
    an open changeset
    """

    pass


class OsmTypeAlreadyExistsError(OsmApiError):
    """
    Error when a user tries to create an object that already exsits
    """

    pass


class XmlResponseInvalidError(OsmApiError):
    """
    Error if the XML response from the OpenStreetMap API is invalid
    """


class ApiError(OsmApiError):
    """
    Error class, is thrown when an API request fails
    """

    def __init__(self, status: int, reason: str, payload: Any) -> None:
        self.status = status
        """HTTP error code"""

        self.reason = reason
        """Error message"""

        self.payload = payload
        """Payload of API when this error occured"""

    @property
    def payload_str(self) -> str:
        """
        The payload decoded as text.

        `payload` is usually the raw `bytes` body of the response; use this
        when the payload needs to be matched against or shown as a string.
        """
        if isinstance(self.payload, bytes):
            return self.payload.decode("utf-8", errors="replace")
        return str(self.payload)

    def __str__(self) -> str:
        return f"Request failed: {self.status} - {self.reason} - {self.payload}"


class UnauthorizedApiError(ApiError):
    """
    Error when the API returned an Unauthorized error,
    e.g. when the provided OAuth token is expired
    """

    pass


class AlreadySubscribedApiError(ApiError):
    """
    Error when a user tries to subscribe to a changeset
    that she is already subscribed to
    """

    pass


class NotSubscribedApiError(ApiError):
    """
    Error when user tries to unsubscribe from a changeset
    that he is not subscribed to
    """

    pass


class ElementDeletedApiError(ApiError):
    """
    Error when the requested element is deleted
    """

    pass


class ElementNotFoundApiError(ApiError):
    """
    Error if the the requested element was not found
    """


class ResponseEmptyApiError(ApiError):
    """
    Error when the response to the request is empty
    """

    pass


class ChangesetClosedApiError(ApiError):
    """
    Error if the the changeset in question has already been closed
    """


class NoteAlreadyClosedApiError(ApiError):
    """
    Error if the the note in question has already been closed
    """


class VersionMismatchApiError(ApiError):
    """
    Error if the provided version does not match the database version
    of the element
    """


class PreconditionFailedApiError(ApiError):
    """
    Error if the precondition of the operation was not met:
    - When a way has nodes that do not exist or are not visible
    - When a relation has elements that do not exist or are not visible
    - When a node/way/relation is still used in a way/relation
    """


class TimeoutApiError(ApiError):
    """
    Error if the http request ran into a timeout
    """


class ConnectionApiError(ApiError):
    """
    Error if there was a network error (e.g. DNS failure, refused connection)
    while connecting to the remote server.
    """


DEPRECATED_ERROR_NAMES = {
    "UsernamePasswordMissingError": "AuthenticationMissingError",
}
"""
Error names that were renamed, mapped to their replacement.

The old names still resolve to the new class (so `except` clauses keep
working), but emit a `DeprecationWarning`. They will be removed in
version 7.0.
"""


def resolve_deprecated_name(name: str) -> Any:
    """
    Return the error class a deprecated name refers to, with a warning.

    Raises `AttributeError` if `name` is not a deprecated error name. The
    `DeprecationWarning` is reported against the caller of the module-level
    `__getattr__` that calls this, i.e. the code using the old name.
    """
    new_name = DEPRECATED_ERROR_NAMES.get(name)
    if not new_name:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    warnings.warn(
        f"{name} has been renamed to {new_name}, "
        f"the old name is deprecated and will be removed in osmapi 7.0",
        DeprecationWarning,
        stacklevel=3,
    )
    return globals()[new_name]


def __getattr__(name: str) -> Any:
    """
    Resolve a deprecated error name to its replacement (see PEP 562).

    Accessing `osmapi.errors.UsernamePasswordMissingError` returns
    `AuthenticationMissingError` and emits a `DeprecationWarning`.
    """
    return resolve_deprecated_name(name)
