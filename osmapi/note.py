"""
Note operations for the OpenStreetMap API.
"""

from typing import Any, TYPE_CHECKING

from . import dom, errors, parser

if TYPE_CHECKING:
    from .OsmApi import OsmApi


class NoteMixin:
    """Mixin providing note-related operations with pythonic method names."""

    def notes_get(
        self: "OsmApi",
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        limit: int = 100,
        closed: int = 7,
    ) -> list[dict[str, Any]]:
        """
        Returns a list of dicts of notes in the specified bounding box.

        The limit parameter defines how many results should be returned.

        closed specifies the number of days a bug needs to be closed
        to no longer be returned.
        The value 0 means only open bugs are returned,
        -1 means all bugs are returned.

        All parameters are optional.
        """
        path = "/api/0.6/notes"
        params = {
            "bbox": f"{min_lon:f},{min_lat:f},{max_lon:f},{max_lat:f}",
            "limit": limit,
            "closed": closed,
        }
        data = self._session._get(path, params=params)
        return parser.parse_notes(data)

    def note_get(self: "OsmApi", note_id: int) -> dict[str, Any]:
        """
        Returns a note as dict.

        `note_id` is the unique identifier of the note.
        """
        uri = f"/api/0.6/notes/{note_id}"
        data = self._session._get(uri)
        note_element = dom.OsmResponseToDom(data, tag="note", single=True)
        return dom.dom_parse_note(note_element)

    def note_create(self: "OsmApi", note_data: dict[str, Any]) -> dict[str, Any]:
        """
        Creates a note based on the supplied `note_data` dict:

            #!python
            {
                'lat': latitude of note,
                'lon': longitude of note,
                'text': text of the note,
            }

        Returns updated note data.
        """
        uri = "/api/0.6/notes"
        return self._note_action(uri, params=note_data)

    def note_comment(self: "OsmApi", note_id: int, comment: str) -> dict[str, Any]:
        """
        Adds a new comment to a note.

        Returns the updated note.
        """
        path = f"/api/0.6/notes/{note_id}/comment"
        return self._note_action(path, comment)

    def note_close(
        self: "OsmApi", note_id: int, comment: str | None = None
    ) -> dict[str, Any]:
        """
        Closes a note.

        Returns the updated note.

        If no session is provided to authenticate the request,
        `OsmApi.AuthenticationMissingError` is raised.
        """
        path = f"/api/0.6/notes/{note_id}/close"
        return self._note_action(path, comment, optional_auth=False)

    def note_reopen(
        self: "OsmApi", note_id: int, comment: str | None = None
    ) -> dict[str, Any]:
        """
        Reopens a note.

        Returns the updated note.

        If no session is provided to authenticate the request,
        `OsmApi.AuthenticationMissingError` is raised.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        path = f"/api/0.6/notes/{note_id}/reopen"
        return self._note_action(path, comment, optional_auth=False)

    def notes_search(
        self: "OsmApi", query: str, limit: int = 100, closed: int = 7
    ) -> list[dict[str, Any]]:
        """
        Returns a list of dicts of notes that match the given search query.

        The limit parameter defines how many results should be returned.

        closed specifies the number of days a bug needs to be closed
        to no longer be returned.
        The value 0 means only open bugs are returned,
        -1 means all bugs are returned.
        """
        uri = "/api/0.6/notes/search"
        params: dict[str, Any] = {
            "q": query,
            "limit": limit,
            "closed": closed,
        }
        data = self._session._get(uri, params=params)
        return parser.parse_notes(data)

    def _note_action(
        self: "OsmApi",
        path: str,
        comment: str | None = None,
        optional_auth: bool = True,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Performs an action on a Note with a comment

        Return the updated note
        """
        uri = path
        final_params = params.copy() if params else {}
        if comment is not None:
            final_params["text"] = comment
        try:
            result = self._session._post(
                uri,
                None,
                optionalAuth=optional_auth,
                params=final_params if final_params else None,
            )
        except errors.ApiError as e:
            if e.status == 409:
                raise errors.NoteAlreadyClosedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise

        # parse the result
        note_element = dom.OsmResponseToDom(result, tag="note", single=True)
        return dom.dom_parse_note(note_element)
