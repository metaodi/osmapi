"""
Changeset operations for the OpenStreetMap API.
"""

import re
import urllib.parse
import xml.dom.minidom
import xml.parsers.expat
from contextlib import contextmanager
from collections.abc import Generator
from typing import Any, TYPE_CHECKING, cast
from xml.dom.minidom import Element

from . import dom, errors, xmlbuilder, parser

if TYPE_CHECKING:
    from .OsmApi import OsmApi


class ChangesetMixin:
    """Mixin providing changeset-related operations with pythonic method names."""

    @contextmanager
    def changeset(
        self: "OsmApi", changeset_tags: dict[str, str] | None = None
    ) -> Generator[int, None, None]:
        """
        Context manager for a Changeset.

        It opens a Changeset, uploads the changes and closes the changeset
        when used with the `with` statement:

            #!python
            import osmapi

            with api.changeset({"comment": "Import script XYZ"}) as changeset_id:
                print(f"Part of changeset {changeset_id}")
                api.node_create({"lon":1, "lat":1, "tag": {}})

        If `changeset_tags` are given, this tags are applied (key/value).

        Returns `changeset_id`

        The changeset is closed on the way out even if the body raises, so
        that an error does not leave a changeset dangling and block the next
        one with an `OsmApi.ChangesetAlreadyOpenError`.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.
        """
        if changeset_tags is None:
            changeset_tags = {}
        # Create a new changeset
        changeset_id = self.changeset_create(changeset_tags)
        try:
            yield changeset_id
        finally:
            self.changeset_close()

    def changeset_get(
        self: "OsmApi", changeset_id: int, include_discussion: bool = False
    ) -> dict[str, Any]:
        """
        Returns changeset with `changeset_id` as a dict.

        `changeset_id` is the unique identifier of a changeset.

        If `include_discussion` is set to `True` the changeset discussion
        will be available in the result.
        """
        path = f"/api/0.6/changeset/{changeset_id}"
        if include_discussion:
            path = f"{path}?include_discussion=true"
        data = self._session._get(path)
        changeset = cast(
            Element, dom.OsmResponseToDom(data, tag="changeset", single=True)
        )
        return dom.dom_parse_changeset(changeset, include_discussion=include_discussion)

    def changeset_update(
        self: "OsmApi", changeset_tags: dict[str, str] | None = None
    ) -> int:
        """
        Updates current changeset with `changeset_tags`.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        if changeset_tags is None:
            changeset_tags = {}
        if not self._current_changeset_id:
            raise errors.NoChangesetOpenError("No changeset currently opened")
        if "created_by" not in changeset_tags:
            changeset_tags["created_by"] = self._created_by
        try:
            self._session._put(
                f"/api/0.6/changeset/{self._current_changeset_id}",
                xmlbuilder._xml_build("changeset", {"tag": changeset_tags}, data=self),
                return_value=False,
            )
        except errors.ApiError as e:
            if e.status == 409:
                raise errors.ChangesetClosedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise
        return self._current_changeset_id

    def changeset_create(
        self: "OsmApi", changeset_tags: dict[str, str] | None = None
    ) -> int:
        """
        Opens a changeset.

        If `changeset_tags` are given, this tags are applied (key/value).

        Returns `changeset_id`

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.
        """
        if changeset_tags is None:
            changeset_tags = {}
        if self._current_changeset_id:
            raise errors.ChangesetAlreadyOpenError("Changeset already opened")
        if "created_by" not in changeset_tags:
            changeset_tags["created_by"] = self._created_by

        # check if someone tries to create a test changeset to PROD
        if (
            self._api == "https://www.openstreetmap.org"
            and changeset_tags.get("comment") == "My first test"
        ):
            raise errors.OsmApiError(
                "DO NOT CREATE test changesets on the production server"
            )

        result = self._session._put(
            "/api/0.6/changeset/create",
            xmlbuilder._xml_build("changeset", {"tag": changeset_tags}, data=self),
        )
        self._current_changeset_id = int(result)
        return self._current_changeset_id

    def changeset_close(self: "OsmApi") -> int:
        """
        Closes current changeset.

        Returns `changeset_id`.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        if not self._current_changeset_id:
            raise errors.NoChangesetOpenError("No changeset currently opened")
        try:
            self._session._put(
                f"/api/0.6/changeset/{self._current_changeset_id}/close",
                None,
                return_value=False,
            )
            current_changeset_id = self._current_changeset_id
            self._current_changeset_id = 0
        except errors.ApiError as e:
            if e.status == 409:
                raise errors.ChangesetClosedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise
        return current_changeset_id

    def changeset_upload(
        self: "OsmApi", changes_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Upload data with the `changes_data` list of dicts.

        Returns list with updated ids.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        data = ""
        data += '<?xml version="1.0" encoding="UTF-8"?>\n'
        data += '<osmChange version="0.6" generator="'
        data += self._created_by + '">\n'
        for change in changes_data:
            data += "<" + change["action"] + ">\n"
            change_data = change["data"]
            data += self._add_changeset_data(change_data, change["type"])
            data += "</" + change["action"] + ">\n"
        data += "</osmChange>"
        try:
            response_data = self._session._post(
                f"/api/0.6/changeset/{self._current_changeset_id}/upload",
                data.encode("utf-8"),
                forceAuth=True,
            )
        except errors.ApiError as e:
            if e.status == 409 and re.search(
                r"The changeset .* was closed at .*", e.payload_str
            ):
                raise errors.ChangesetClosedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise
        try:
            result_dom = xml.dom.minidom.parseString(response_data)
            diff_result = result_dom.getElementsByTagName("diffResult")[0]
            result_elements = [
                x for x in diff_result.childNodes if x.nodeType == x.ELEMENT_NODE
            ]
        except (xml.parsers.expat.ExpatError, IndexError) as e:
            raise errors.XmlResponseInvalidError(
                f"The XML response from the OSM API is invalid: {e!r}"
            ) from e

        for change in changes_data:
            if change["action"] == "delete":
                for change_element in change["data"]:
                    change_element.pop("version")
            else:
                self._assign_id_and_version(result_elements, change["data"])

        return changes_data

    def changeset_download(self: "OsmApi", changeset_id: int) -> list[dict[str, Any]]:
        """
        Download data from changeset `changeset_id`.

        Returns list of dict with type, action, and data.
        """
        uri = f"/api/0.6/changeset/{changeset_id}/download"
        data = self._session._get(uri)
        return parser.parse_osc(data)

    def changesets_get(  # noqa: C901
        self: "OsmApi",
        min_lon: float | None = None,
        min_lat: float | None = None,
        max_lon: float | None = None,
        max_lat: float | None = None,
        userid: int | None = None,
        username: str | None = None,
        closed_after: str | None = None,
        created_before: str | None = None,
        only_open: bool = False,
        only_closed: bool = False,
    ) -> dict[int, dict[str, Any]]:
        """
        Returns a dict with the id of the changeset as key matching all criteria.

        All parameters are optional. The bounding box is only applied if all
        four of `min_lon`, `min_lat`, `max_lon` and `max_lat` are given.

        If only some of the bounding box values are given,
        `ValueError` is raised.
        """
        uri = "/api/0.6/changesets"
        params: dict[str, Any] = {}
        bbox = (min_lon, min_lat, max_lon, max_lat)
        if any(coord is not None for coord in bbox):
            if any(coord is None for coord in bbox):
                raise ValueError(
                    "A bounding box needs all of min_lon, min_lat, max_lon "
                    "and max_lat, got "
                    f"min_lon={min_lon}, min_lat={min_lat}, "
                    f"max_lon={max_lon}, max_lat={max_lat}"
                )
            params["bbox"] = ",".join(str(coord) for coord in bbox)
        if userid:
            params["user"] = userid
        if username:
            params["display_name"] = username
        if closed_after and not created_before:
            params["time"] = closed_after
        if created_before:
            if not closed_after:
                closed_after = "1970-01-01T00:00:00Z"
            params["time"] = f"{closed_after},{created_before}"
        if only_open:
            params["open"] = 1
        if only_closed:
            params["closed"] = 1

        if params:
            uri += "?" + urllib.parse.urlencode(params)

        data = self._session._get(uri)
        changesets = cast(list[Element], dom.OsmResponseToDom(data, tag="changeset"))
        result: dict[int, dict[str, Any]] = {}
        for cur_changeset in changesets:
            tmp_cs = dom.dom_parse_changeset(cur_changeset)
            result[tmp_cs["id"]] = tmp_cs
        return result

    def changeset_comment(
        self: "OsmApi", changeset_id: int, comment: str
    ) -> dict[str, Any]:
        """
        Adds a comment to the changeset `changeset_id`.

        `comment` should be a string.

        Returns the updated changeset data dict.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        params = urllib.parse.urlencode({"text": comment})
        try:
            data = self._session._post(
                f"/api/0.6/changeset/{changeset_id}/comment",
                params,
                forceAuth=True,
            )
        except errors.ApiError as e:
            if e.status == 409:
                raise errors.ChangesetClosedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise
        changeset = cast(
            Element,
            dom.OsmResponseToDom(data, tag="changeset", single=True),
        )
        return dom.dom_parse_changeset(changeset, include_discussion=False)

    def changeset_subscribe(self: "OsmApi", changeset_id: int) -> dict[str, Any]:
        """
        Subscribe to the changeset `changeset_id`.

        Returns the updated changeset data dict.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If already subscribed to this changeset,
        `OsmApi.AlreadySubscribedApiError` is raised.
        """
        try:
            data = self._session._post(
                f"/api/0.6/changeset/{changeset_id}/subscribe",
                None,
                forceAuth=True,
            )
        except errors.ApiError as e:
            if e.status == 409:
                raise errors.AlreadySubscribedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise
        changeset = cast(
            Element,
            dom.OsmResponseToDom(data, tag="changeset", single=True),
        )
        return dom.dom_parse_changeset(changeset, include_discussion=False)

    def changeset_unsubscribe(self: "OsmApi", changeset_id: int) -> dict[str, Any]:
        """
        Unsubscribe from the changeset `changeset_id`.

        Returns the updated changeset data dict.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If not subscribed to this changeset,
        `OsmApi.NotSubscribedApiError` is raised.
        """
        try:
            data = self._session._post(
                f"/api/0.6/changeset/{changeset_id}/unsubscribe",
                None,
                forceAuth=True,
            )
        except errors.ApiError as e:
            if e.status == 404:
                raise errors.NotSubscribedApiError(e.status, e.reason, e.payload) from e
            else:
                raise
        changeset = cast(
            Element,
            dom.OsmResponseToDom(data, tag="changeset", single=True),
        )
        return dom.dom_parse_changeset(changeset, include_discussion=False)
