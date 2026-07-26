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
* All method names are in snake_case. The deprecated CamelCase versions
(e.g. `NodeGet`) were removed in version 6.0.
"""

import re
import logging
from typing import Any, NoReturn
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
        appid: str = "",
        created_by: str = f"osmapi/{__version__}",
        api: str = "https://www.openstreetmap.org",
        session: requests.Session | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialized the OsmApi object.

        To make authenticated requests (i.e. anything that writes to OSM),
        pass an authenticated `requests.Session` as the `session` parameter,
        see below. Username/password authentication was shut down by
        OpenStreetMap in July 2024 and the corresponding parameters
        (`username`, `password` and `passwordfile`) were removed in
        version 6.0 of osmapi, use OAuth 2.0 instead.

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
        http session object (requests.Session). This is how authentication
        is provided: a session whose `auth` is set (e.g. by an OAuth 2.0
        library) is used for authenticated requests. It is also useful for
        custom adapters, hooks etc.

        Finally the `timeout` parameter is used by the http session to
        throw an expcetion if the the timeout (in seconds) has passed without
        an answer from the server.
        """
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
        self.http_session: requests.Session | None = session
        self._timeout: int = timeout
        self._session: http.OsmApiSession = http.OsmApiSession(
            self._api,
            self._created_by,
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
    # Internal method                                #
    ##################################################

    def _raise_write_error(self, e: errors.ApiError) -> NoReturn:
        """
        Translate an `ApiError` raised by an element write into a typed error.

        A 409 means either that the changeset has since been closed or that the
        element version is out of date; a 412 means a precondition (usually a
        referenced element) was not met. Anything else is re-raised unchanged.
        """
        if e.status == 409:
            if re.search(r"The changeset .* was closed at .*", e.payload_str):
                raise errors.ChangesetClosedApiError(
                    e.status, e.reason, e.payload
                ) from e
            raise errors.VersionMismatchApiError(e.status, e.reason, e.payload) from e
        elif e.status == 412:
            raise errors.PreconditionFailedApiError(
                e.status, e.reason, e.payload
            ) from e
        raise e

    def _do(  # type: ignore[return-value]
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
            return self._do_create(osm_type, osm_data)
        elif action == "modify":
            return self._do_modify(osm_type, osm_data)
        elif action == "delete":
            return self._do_delete(osm_type, osm_data)

    def _do_create(self, osm_type: str, osm_data: dict[str, Any]) -> dict[str, Any]:
        if osm_data.get("id", -1) > 0:
            raise errors.OsmTypeAlreadyExistsError(f"This {osm_type} already exists")
        try:
            result = self._session._put(
                f"/api/0.6/{osm_type}/create",
                xmlbuilder._xml_build(osm_type, osm_data, data=self),
            )
        except errors.ApiError as e:
            self._raise_write_error(e)
        osm_data["id"] = int(result.strip())
        osm_data["version"] = 1
        return osm_data

    def _do_modify(self, osm_type: str, osm_data: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._session._put(
                f"/api/0.6/{osm_type}/{osm_data['id']}",
                xmlbuilder._xml_build(osm_type, osm_data, data=self),
            )
        except errors.ApiError as e:
            logger.error(e.reason)
            self._raise_write_error(e)
        osm_data["version"] = int(result.strip())
        return osm_data

    def _do_delete(self, osm_type: str, osm_data: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._session._delete(
                f"/api/0.6/{osm_type}/{osm_data['id']}",
                xmlbuilder._xml_build(osm_type, osm_data, data=self),
            )
        except errors.ApiError as e:
            self._raise_write_error(e)
        osm_data["version"] = int(result.strip())
        osm_data["visible"] = False
        return osm_data

    def _add_changeset_data(self, change_data: list[dict[str, Any]], type: str) -> str:
        data = ""
        for changed_element in change_data:
            changed_element["changeset"] = self._current_changeset_id
            xml_data = xmlbuilder._xml_build(type, changed_element, False, data=self)
            data += xml_data.decode("utf-8")
        return data

    def _assign_id_and_version(
        self, response_data: list[Element], request_data: list[dict[str, Any]]
    ) -> None:
        for response, element in zip(response_data, request_data):
            element["id"] = int(response.getAttribute("new_id"))
            element["version"] = int(response.getAttribute("new_version"))
