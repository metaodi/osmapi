"""
The OsmApi module is a wrapper for the OpenStreetMap API.
As such it provides an easy access to the functionality of the API.

You can find this module [on PyPI](https://pypi.python.org/pypi/osmapi)
or [on GitHub](https://github.com/metaodi/osmapi).

Find all information about changes of the different versions of this module
[in the CHANGELOG](https://github.com/metaodi/osmapi/blob/master/CHANGELOG.md).


## Notes:

* **dictionary keys** are _unicode_
* **changeset** is _integer_
* **version** is _integer_
* **tag** is a _dictionary_
* **timestamp** is _unicode_
* **user** is _unicode_
* **uid** is _integer_
* node **lat** and **lon** are _floats_
* way **nd** is list of _integers_
* relation **member** is a _list of dictionaries_ like
`{"role": "", "ref":123, "type": "node"}`
* Since version 5.0 of this library, all method names are in snake_case,
the CamelCase versions are deprecated and will be removed in version 6.0.
"""

import re
import logging
import warnings
from contextlib import contextmanager
from typing import Any, Optional, Generator
from xml.dom.minidom import Element
import requests

from osmapi import __version__
from . import errors
from . import http
from . import xmlbuilder
from .node import NodeMixin
from .way import WayMixin
from .relation import RelationMixin
from .changeset import ChangesetMixin
from .note import NoteMixin
from .capabilities import CapabilitiesMixin

logger = logging.getLogger(__name__)


class OsmApi(
    NodeMixin,
    WayMixin,
    RelationMixin,
    ChangesetMixin,
    NoteMixin,
    CapabilitiesMixin,
):
    """
    Main class of osmapi, instanciate this class to use osmapi
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        passwordfile: Optional[str] = None,
        appid: str = "",
        created_by: str = f"osmapi/{__version__}",
        api: str = "https://www.openstreetmap.org",
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialized the OsmApi object.

        There are two different ways to authenticate a user.
        Either `username` and `password` are supplied directly or the path
        to a `passwordfile` is given, where on the first line username
        and password must be colon-separated (<user>:<pass>).

        To credit the application that supplies changes to OSM, an `appid`
        can be provided.  This is a string identifying the application.
        If this is omitted "osmapi" is used.

        It is possible to configure the URL to connect to using the `api`
        parameter.  By default this is the SSL version of the production API
        of OpenStreetMap, for testing purposes, one might prefer the official
        test instance at "api06.dev.openstreetmap.org" or any other valid
        OSM-API. To use an encrypted connection (HTTPS) simply add 'https://'
        in front of the hostname of the `api` parameter (e.g.
        https://api.openstreetmap.com).

        The `session` parameter can be used to provide a custom requests
        http session object (requests.Session). This might be useful for
        OAuth authentication, custom adapters, hooks etc.

        Finally the `timeout` parameter is used by the http session to
        throw an expcetion if the the timeout (in seconds) has passed without
        an answer from the server.
        """
        # Get username
        self._username: Optional[str] = None
        if username:
            self._username = username
        elif passwordfile:
            with open(passwordfile) as f:
                pass_line = f.readline()
            self._username = pass_line.partition(":")[0].strip()

        # Get password
        self._password: Optional[str] = None
        if password:
            self._password = password
        elif passwordfile:
            with open(passwordfile) as f:
                for line in f:
                    key, _, value = line.strip().partition(":")
                    if key == self._username:
                        self._password = value

        # Get API
        self._api: str = api.strip("/")

        # Get created_by
        if not appid:
            self._created_by: str = created_by
        else:
            self._created_by = f"{appid} ({created_by})"

        # Initialisation
        self._current_changeset_id: int = 0

        # Http connection
        self.http_session: Optional[requests.Session] = session
        self._timeout: int = timeout
        auth: Optional[tuple[str, str]] = None
        if self._username and self._password:
            auth = (self._username, self._password)
        self._session: http.OsmApiSession = http.OsmApiSession(
            self._api,
            self._created_by,
            auth=auth,
            session=self.http_session,
            timeout=self._timeout,
        )

    def __enter__(self) -> "OsmApi":
        self._session = http.OsmApiSession(
            self._api,
            self._created_by,
            session=self.http_session,
            timeout=self._timeout,
        )
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        if self._session:
            self._session.close()

    ##################################################
    # Capabilities                                   #
    ##################################################

    def Capabilities(self) -> dict[str, dict[str, Any]]:
        """
        Returns the API capabilities as a dict.

        .. deprecated::
            Use :meth:`capabilities` instead.

        The capabilities can be used by a client to
        gain insights of the server in use.
        """
        warnings.warn(
            "Capabilities() is deprecated, use capabilities() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.capabilities()

    ##################################################
    # Node - Deprecated CamelCase methods           #
    ##################################################

    def NodeGet(self, NodeId: int, NodeVersion: int = -1) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`node_get` instead."""
        warnings.warn(
            "NodeGet() is deprecated, use node_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_get(NodeId, NodeVersion)

    def NodeCreate(self, NodeData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_create` instead."""
        warnings.warn(
            "NodeCreate() is deprecated, use node_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_create(NodeData)

    def NodeUpdate(self, NodeData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_update` instead."""
        warnings.warn(
            "NodeUpdate() is deprecated, use node_update() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_update(NodeData)

    def NodeDelete(self, NodeData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_delete` instead."""
        warnings.warn(
            "NodeDelete() is deprecated, use node_delete() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_delete(NodeData)

    def NodeHistory(self, NodeId: int) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_history` instead."""
        warnings.warn(
            "NodeHistory() is deprecated, use node_history() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_history(NodeId)

    def NodeWays(self, NodeId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_ways` instead."""
        warnings.warn(
            "NodeWays() is deprecated, use node_ways() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_ways(NodeId)

    def NodeRelations(self, NodeId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_relations` instead."""
        warnings.warn(
            "NodeRelations() is deprecated, use node_relations() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_relations(NodeId)

    def NodesGet(self, NodeIdList: list[int]) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`nodes_get` instead."""
        warnings.warn(
            "NodesGet() is deprecated, use nodes_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.nodes_get(NodeIdList)

    ##################################################
    # Way - Deprecated CamelCase methods            #
    ##################################################

    def WayGet(self, WayId: int, WayVersion: int = -1) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`way_get` instead."""
        warnings.warn(
            "WayGet() is deprecated, use way_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_get(WayId, WayVersion)

    def WayCreate(self, WayData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_create` instead."""
        warnings.warn(
            "WayCreate() is deprecated, use way_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_create(WayData)

    def WayUpdate(self, WayData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_update` instead."""
        warnings.warn(
            "WayUpdate() is deprecated, use way_update() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_update(WayData)

    def WayDelete(self, WayData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_delete` instead."""
        warnings.warn(
            "WayDelete() is deprecated, use way_delete() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_delete(WayData)

    def WayHistory(self, WayId: int) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_history` instead."""
        warnings.warn(
            "WayHistory() is deprecated, use way_history() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_history(WayId)

    def WayRelations(self, WayId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_relations` instead."""
        warnings.warn(
            "WayRelations() is deprecated, use way_relations() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_relations(WayId)

    def WayFull(self, WayId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_full` instead."""
        warnings.warn(
            "WayFull() is deprecated, use way_full() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_full(WayId)

    def WaysGet(self, WayIdList: list[int]) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`ways_get` instead."""
        warnings.warn(
            "WaysGet() is deprecated, use ways_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.ways_get(WayIdList)

    ##################################################
    # Relation - Deprecated CamelCase methods       #
    ##################################################

    def RelationGet(self, RelationId: int, RelationVersion: int = -1) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`relation_get` instead."""
        warnings.warn(
            "RelationGet() is deprecated, use relation_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_get(RelationId, RelationVersion)

    def RelationCreate(self, RelationData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_create` instead."""
        warnings.warn(
            "RelationCreate() is deprecated, use relation_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_create(RelationData)

    def RelationUpdate(self, RelationData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_update` instead."""
        warnings.warn(
            "RelationUpdate() is deprecated, use relation_update() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_update(RelationData)

    def RelationDelete(self, RelationData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_delete` instead."""
        warnings.warn(
            "RelationDelete() is deprecated, use relation_delete() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_delete(RelationData)

    def RelationHistory(self, RelationId: int) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_history` instead."""
        warnings.warn(
            "RelationHistory() is deprecated, use relation_history() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_history(RelationId)

    def RelationRelations(self, RelationId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_relations` instead."""
        warnings.warn(
            "RelationRelations() is deprecated, use relation_relations() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_relations(RelationId)

    def RelationFullRecur(self, RelationId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_full_recur` instead."""
        warnings.warn(
            "RelationFullRecur() is deprecated, use relation_full_recur() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_full_recur(RelationId)

    def RelationFull(self, RelationId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_full` instead."""
        warnings.warn(
            "RelationFull() is deprecated, use relation_full() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_full(RelationId)

    def RelationsGet(self, RelationIdList: list[int]) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`relations_get` instead."""
        warnings.warn(
            "RelationsGet() is deprecated, use relations_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relations_get(RelationIdList)

    ##################################################
    # Changeset - Deprecated CamelCase methods      #
    ##################################################

    @contextmanager
    def Changeset(
        self, ChangesetTags: Optional[dict[str, str]] = None
    ) -> Generator[int, None, None]:
        """.. deprecated:: Use :meth:`changeset` instead."""
        warnings.warn(
            "Changeset() is deprecated, use changeset() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        with self.changeset(ChangesetTags) as changeset_id:
            yield changeset_id

    def ChangesetGet(
        self, ChangesetId: int, include_discussion: bool = False
    ) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`changeset_get` instead."""
        warnings.warn(
            "ChangesetGet() is deprecated, use changeset_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_get(ChangesetId, include_discussion)

    def ChangesetUpdate(self, ChangesetTags: Optional[dict[str, str]] = None) -> int:
        """.. deprecated:: Use :meth:`changeset_update` instead."""
        warnings.warn(
            "ChangesetUpdate() is deprecated, use changeset_update() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_update(ChangesetTags)

    def ChangesetCreate(self, ChangesetTags: Optional[dict[str, str]] = None) -> int:
        """.. deprecated:: Use :meth:`changeset_create` instead."""
        warnings.warn(
            "ChangesetCreate() is deprecated, use changeset_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_create(ChangesetTags)

    def ChangesetClose(self) -> int:
        """.. deprecated:: Use :meth:`changeset_close` instead."""
        warnings.warn(
            "ChangesetClose() is deprecated, use changeset_close() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_close()

    def ChangesetUpload(
        self, ChangesData: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`changeset_upload` instead."""
        warnings.warn(
            "ChangesetUpload() is deprecated, use changeset_upload() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_upload(ChangesData)

    def ChangesetDownload(self, ChangesetId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`changeset_download` instead."""
        warnings.warn(
            "ChangesetDownload() is deprecated, use changeset_download() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_download(ChangesetId)

    def ChangesetsGet(  # noqa
        self,
        min_lon: Optional[float] = None,
        min_lat: Optional[float] = None,
        max_lon: Optional[float] = None,
        max_lat: Optional[float] = None,
        userid: Optional[int] = None,
        username: Optional[str] = None,
        closed_after: Optional[str] = None,
        created_before: Optional[str] = None,
        only_open: bool = False,
        only_closed: bool = False,
    ) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`changesets_get` instead."""
        warnings.warn(
            "ChangesetsGet() is deprecated, use changesets_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changesets_get(
            min_lon,
            min_lat,
            max_lon,
            max_lat,
            userid,
            username,
            closed_after,
            created_before,
            only_open,
            only_closed,
        )

    def ChangesetComment(self, ChangesetId: int, comment: str) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`changeset_comment` instead."""
        warnings.warn(
            "ChangesetComment() is deprecated, use changeset_comment() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_comment(ChangesetId, comment)

    def ChangesetSubscribe(self, ChangesetId: int) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`changeset_subscribe` instead."""
        warnings.warn(
            "ChangesetSubscribe() is deprecated, use changeset_subscribe() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_subscribe(ChangesetId)

    def ChangesetUnsubscribe(self, ChangesetId: int) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`changeset_unsubscribe` instead."""
        warnings.warn(
            "ChangesetUnsubscribe() is deprecated, use changeset_unsubscribe() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_unsubscribe(ChangesetId)

    ##################################################
    # Note - Deprecated CamelCase methods           #
    ##################################################

    def NotesGet(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        limit: int = 100,
        closed: int = 7,
    ) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`notes_get` instead."""
        warnings.warn(
            "NotesGet() is deprecated, use notes_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.notes_get(min_lon, min_lat, max_lon, max_lat, limit, closed)

    def NoteGet(self, id: int) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_get` instead."""
        warnings.warn(
            "NoteGet() is deprecated, use note_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_get(id)

    def NoteCreate(self, NoteData: dict[str, Any]) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_create` instead."""
        warnings.warn(
            "NoteCreate() is deprecated, use note_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_create(NoteData)

    def NoteComment(self, note_id: int, comment: str) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_comment` instead."""
        warnings.warn(
            "NoteComment() is deprecated, use note_comment() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_comment(note_id, comment)

    def NoteClose(self, note_id: int, comment: Optional[str] = None) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_close` instead."""
        warnings.warn(
            "NoteClose() is deprecated, use note_close() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_close(note_id, comment)

    def NoteReopen(self, note_id: int, comment: Optional[str] = None) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_reopen` instead."""
        warnings.warn(
            "NoteReopen() is deprecated, use note_reopen() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_reopen(note_id, comment)

    def NotesSearch(
        self, query: str, limit: int = 100, closed: int = 7
    ) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`notes_search` instead."""
        warnings.warn(
            "NotesSearch() is deprecated, use notes_search() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.notes_search(query, limit, closed)

    def _NoteAction(
        self, path: str, comment: Optional[str] = None, optionalAuth: bool = True
    ) -> dict[str, Any]:
        """Internal method - calls _note_action."""
        return self._note_action(path, comment, optionalAuth)

    ##################################################
    # Map - Deprecated CamelCase methods            #
    ##################################################

    def Map(
        self, min_lon: float, min_lat: float, max_lon: float, max_lat: float
    ) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`map` instead."""
        warnings.warn(
            "Map() is deprecated, use map() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.map(min_lon, min_lat, max_lon, max_lat)

    ##################################################
    # Internal method                                #
    ##################################################

    def _do(  # type: ignore[return-value]  # noqa: C901
        self, action: str, osm_type: str, osm_data: dict[str, Any]
    ) -> dict[str, Any]:
        if not self._current_changeset_id:
            raise errors.NoChangesetOpenError(
                "You need to open a changeset before uploading data"
            )
        if "timestamp" in osm_data:
            osm_data.pop("timestamp")
        osm_data["changeset"] = self._current_changeset_id
        if action == "create":
            if osm_data.get("id", -1) > 0:
                raise errors.OsmTypeAlreadyExistsError(f"This {osm_type} already exists")
            try:
                result = self._session._put(
                    f"/api/0.6/{osm_type}/create",
                    xmlbuilder._xml_build(osm_type, osm_data, data=self),
                )
            except errors.ApiError as e:
                if e.status == 409 and re.search(
                    r"The changeset .* was closed at .*", e.payload
                ):
                    raise errors.ChangesetClosedApiError(
                        e.status, e.reason, e.payload
                    ) from e
                elif e.status == 409:
                    raise errors.VersionMismatchApiError(
                        e.status, e.reason, e.payload
                    ) from e
                elif e.status == 412:
                    raise errors.PreconditionFailedApiError(
                        e.status, e.reason, e.payload
                    ) from e
                else:
                    raise
            osm_data["id"] = int(result.strip())
            osm_data["version"] = 1
            return osm_data
        elif action == "modify":
            try:
                result = self._session._put(
                    f"/api/0.6/{osm_type}/{osm_data['id']}",
                    xmlbuilder._xml_build(osm_type, osm_data, data=self),
                )
            except errors.ApiError as e:
                logger.error(e.reason)
                if e.status == 409 and re.search(
                    r"The changeset .* was closed at .*", e.payload
                ):
                    raise errors.ChangesetClosedApiError(
                        e.status, e.reason, e.payload
                    ) from e
                elif e.status == 409:
                    raise errors.VersionMismatchApiError(
                        e.status, e.reason, e.payload
                    ) from e
                elif e.status == 412:
                    raise errors.PreconditionFailedApiError(
                        e.status, e.reason, e.payload
                    ) from e
                else:
                    raise
            osm_data["version"] = int(result.strip())
            return osm_data
        elif action == "delete":
            try:
                result = self._session._delete(
                    f"/api/0.6/{osm_type}/{osm_data['id']}",
                    xmlbuilder._xml_build(osm_type, osm_data, data=self),
                )
            except errors.ApiError as e:
                if e.status == 409 and re.search(
                    r"The changeset .* was closed at .*", e.payload
                ):
                    raise errors.ChangesetClosedApiError(
                        e.status, e.reason, e.payload
                    ) from e
                elif e.status == 409:
                    raise errors.VersionMismatchApiError(
                        e.status, e.reason, e.payload
                    ) from e
                elif e.status == 412:
                    raise errors.PreconditionFailedApiError(
                        e.status, e.reason, e.payload
                    ) from e
                else:
                    raise
            osm_data["version"] = int(result.strip())
            osm_data["visible"] = False
            return osm_data

    def _add_changeset_data(self, change_data: list[dict[str, Any]], type: str) -> str:
        data = ""
        for changed_element in change_data:
            changed_element["changeset"] = self._current_changeset_id
            data += xmlbuilder._xml_build(type, changed_element, False, data=self).decode(
                "utf-8"
            )
        return data

    def _assign_id_and_version(
        self, response_data: list[Element], request_data: list[dict[str, Any]]
    ) -> None:
        for response, element in zip(response_data, request_data):
            element["id"] = int(response.getAttribute("new_id"))
            element["version"] = int(response.getAttribute("new_version"))
