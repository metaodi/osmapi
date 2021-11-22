# -*- coding: utf-8 -*-

class OsmApiError(Exception):
    """
    General OsmApi error class to provide a superclass for all other errors
    """


class MaximumRetryLimitReachedError(OsmApiError):
    """
    Error when the maximum amount of retries is reached and we have to give up
    """


class UsernamePasswordMissingError(OsmApiError):
    """
    Error when username or password is missing for an authenticated request
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

    def __init__(self, status, reason, payload):
        self.status = status
        """HTTP error code"""

        self.reason = reason
        """Error message"""

        self.payload = payload
        """Payload of API when this error occured"""

    def __str__(self):
        return (
            "Request failed: %s - %s - %s"
            % (str(self.status), self.reason, self.payload)
        )


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


class ResponseEmptyApiError(ApiError):
    """
    Error when the response to the request is empty
    """
    pass


class ChangesetClosedApiError(ApiError):
    """
    Error if the the changeset in question has already been closed
    """


class NoteClosedApiError(ApiError):
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
