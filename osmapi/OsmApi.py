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

"""

import xml.dom.minidom
import xml.parsers.expat
import urllib.parse
import re
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, cast
from xml.dom.minidom import Element
import requests

from osmapi import __version__
from . import dom
from . import errors
from . import http
from . import parser
from . import xmlbuilder

logger = logging.getLogger(__name__)


class OsmApi:
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
        changesetauto: bool = False,
        changesetautotags: Optional[Dict[str, str]] = None,
        changesetautosize: int = 500,
        changesetautomulti: int = 1,
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

        There are several options to control the changeset behaviour. By
        default, a programmer has to take care to open and close a changeset
        prior to make changes to OSM.
        By setting `changesetauto` to `True`, osmapi automatically opens
        changesets.
        The `changesetautotags` parameter takes a `dict`, where each key/value
        pair is applied as tags to the changeset.
        The option `changesetautosize` defines the size of each
        upload (default: 500) and `changesetautomulti` defines how many
        uploads should be made before closing a changeset and opening a new
        one (default: 1).

        The `session` parameter can be used to provide a custom requests
        http session object (requests.Session). This might be useful for
        OAuth authentication, custom adapters, hooks etc.

        Finally the `timeout` parameter is used by the http session to
        throw an expcetion if the the timeout (in seconds) has passed without
        an answer from the server.
        """
        if changesetautotags is None:
            changesetautotags = {}

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

        # Changest informations
        # auto create and close changesets
        self._changesetauto: bool = changesetauto
        # tags for automatic created changesets
        self._changesetautotags: Dict[str, str] = changesetautotags
        # change count for auto changeset
        self._changesetautosize: int = changesetautosize
        # close a changeset every # upload
        self._changesetautomulti: int = changesetautomulti
        self._changesetautocpt: int = 0
        # data to upload for auto group
        self._changesetautodata: List[Dict[str, Any]] = []

        # Get API
        self._api: str = api.strip("/")

        # Get created_by
        if not appid:
            self._created_by: str = created_by
        else:
            self._created_by = f"{appid} ({created_by})"

        # Initialisation
        self._CurrentChangesetId: int = 0

        # Http connection
        self.http_session: Optional[requests.Session] = session
        self._timeout: int = timeout
        auth: Optional[Tuple[str, str]] = None
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
        try:
            if self._changesetauto:
                self._changesetautoflush(True)
        except errors.ResponseEmptyApiError:
            pass

        if self._session:
            self._session.close()

    ##################################################
    # Capabilities                                   #
    ##################################################

    def Capabilities(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns the API capabilities as a dict:

            #!python
            {
                'area': {
                    'maximum': area in square degrees that can be queried,
                },
                'changesets': {
                    'maximum_elements': number of elements per changeset,
                },
                'status': {
                    'api': online|readonly|offline,
                    'database': online|readonly|offline,
                    'gpx': online|readonly|offline,
                },
                'timeout': {
                    'seconds': timeout in seconds for API calls,
                },
                'tracepoints': {
                    'per_page': maximum number of points in a GPX track,
                },
                'version': {
                    'maximum': maximum version of API this server supports,
                    'minimum': minimum version of API this server supports,
                },
                'waynodes': {
                    'maximum': maximum number of nodes that a way may contain,
                },
            }

        The capabilities can be used by a client to
        gain insights of the server in use.
        """
        uri = "/api/capabilities"
        data = self._session._get(uri)

        api_element = cast(Element, dom.OsmResponseToDom(data, tag="api", single=True))
        result: Dict[str, Any] = {}
        for elem in api_element.childNodes:
            if elem.nodeType != elem.ELEMENT_NODE:
                continue
            result[elem.nodeName] = {}
            for k, v in elem.attributes.items():
                try:
                    result[elem.nodeName][k] = float(v)
                except Exception:
                    result[elem.nodeName][k] = v
        return result

    ##################################################
    # Node                                           #
    ##################################################

    def NodeGet(self, NodeId: int, NodeVersion: int = -1) -> Dict[str, Any]:
        """
        Returns node with `NodeId` as a dict:

            #!python
            {
                'id': id of node,
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': {},
                'changeset': id of changeset of last change,
                'version': version number of node,
                'user': username of user that made the last change,
                'uid': id of user that made the last change,
                'timestamp': timestamp of last change,
                'visible': True|False
            }

        If `NodeVersion` is supplied, this specific version is returned,
        otherwise the latest version is returned.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/node/{NodeId}"
        if NodeVersion != -1:
            uri += f"/{NodeVersion}"
        data = self._session._get(uri)
        node_element = cast(
            Element, dom.OsmResponseToDom(data, tag="node", single=True)
        )
        return dom.DomParseNode(node_element)

    def NodeCreate(self, NodeData: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Creates a node based on the supplied `NodeData` dict:

            #!python
            {
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': {},
            }

        Returns updated `NodeData` (without timestamp):

            #!python
            {
                'id': id of node,
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of node,
                'user': username of last change,
                'uid': id of user of last change,
                'visible': True|False
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If the supplied information contain an existing node,
        `OsmApi.OsmTypeAlreadyExistsError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("create", "node", NodeData)

    def NodeUpdate(self, NodeData: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates node with the supplied `NodeData` dict:

            #!python
            {
                'id': id of node,
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': {},
                'version': version number of node,
            }

        Returns updated `NodeData` (without timestamp):

            #!python
            {
                'id': id of node,
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of node,
                'user': username of last change,
                'uid': id of user of last change,
                'visible': True|False
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("modify", "node", NodeData)

    def NodeDelete(self, NodeData: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Delete node with `NodeData`:

            #!python
            {
                'id': id of node,
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': dict of tags,
                'version': version number of node,
            }

        Returns updated `NodeData` (without timestamp):

            #!python
            {
                'id': id of node,
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of node,
                'user': username of last change,
                'uid': id of user of last change,
                'visible': True|False
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.

        If the requested element has already been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        return self._do("delete", "node", NodeData)

    def NodeHistory(self, NodeId: int) -> Dict[int, Dict[str, Any]]:
        """
        Returns dict with version as key:

            #!python
            {
                '1': dict of NodeData,
                '2': dict of NodeData,
                ...
            }

        `NodeId` is the unique identifier of a node.
        """
        uri = f"/api/0.6/node/{NodeId}/history"
        data = self._session._get(uri)
        nodes = cast(List[Element], dom.OsmResponseToDom(data, tag="node"))
        result: Dict[int, Dict[str, Any]] = {}
        for node in nodes:
            node_data = dom.DomParseNode(node)
            result[node_data["version"]] = node_data
        return result

    def NodeWays(self, NodeId: int) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts of `WayData` containing node `NodeId`:

            #!python
            [
                {
                    'id': id of Way,
                    'nd': [] list of NodeIds in this way
                    'tag': {} dict of tags,
                    'changeset': id of changeset of last change,
                    'version': version number of Way,
                    'user': username of user that made the last change,
                    'uid': id of user that made the last change,
                    'visible': True|False
                },
                {
                    ...
                },
            ]

        The `NodeId` is a unique identifier for a node.
        """
        uri = f"/api/0.6/node/{NodeId}/ways"
        data = self._session._get(uri)
        ways = cast(
            List[Element], dom.OsmResponseToDom(data, tag="way", allow_empty=True)
        )
        result: List[Dict[str, Any]] = []
        for way in ways:
            way_data = dom.DomParseWay(way)
            result.append(way_data)
        return result

    def NodeRelations(self, NodeId: int) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts of `RelationData` containing node `NodeId`:

            #!python
            [
                {
                    'id': id of Relation,
                    'member': [
                        {
                            'ref': ID of referenced element,
                            'role': optional description of role in relation
                            'type': node|way|relation
                        },
                        {
                            ...
                        }
                    ]
                    'tag': {},
                    'changeset': id of changeset of last change,
                    'version': version number of Way,
                    'user': username of user that made the last change,
                    'uid': id of user that made the last change,
                    'visible': True|False
                },
                {
                    ...
                },
            ]

        The `NodeId` is a unique identifier for a node.
        """
        uri = f"/api/0.6/node/{NodeId}/relations"
        data = self._session._get(uri)
        relations = cast(
            List[Element], dom.OsmResponseToDom(data, tag="relation", allow_empty=True)
        )
        result: List[Dict[str, Any]] = []
        for relation in relations:
            relation_data = dom.DomParseRelation(relation)
            result.append(relation_data)
        return result

    def NodesGet(self, NodeIdList: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Returns dict with the id of the Node as a key
        for each node in `NodeIdList`:

            #!python
            {
                '1234': dict of NodeData,
                '5678': dict of NodeData,
                ...
            }

        `NodeIdList` is a list containing unique identifiers
        for multiple nodes.
        """
        node_list = ",".join([str(x) for x in NodeIdList])
        uri = f"/api/0.6/nodes?nodes={node_list}"
        data = self._session._get(uri)
        nodes = cast(List[Element], dom.OsmResponseToDom(data, tag="node"))
        result: Dict[int, Dict[str, Any]] = {}
        for node in nodes:
            node_data = dom.DomParseNode(node)
            result[node_data["id"]] = node_data
        return result

    ##################################################
    # Way                                            #
    ##################################################

    def WayGet(self, WayId: int, WayVersion: int = -1) -> Dict[str, Any]:
        """
        Returns way with `WayId` as a dict:

            #!python
            {
                'id': id of way,
                'tag': {} tags of this way,
                'nd': [] list of nodes belonging to this way
                'changeset': id of changeset of last change,
                'version': version number of way,
                'user': username of user that made the last change,
                'uid': id of user that made the last change,
                'timestamp': timestamp of last change,
                'visible': True|False
            }

        If `WayVersion` is supplied, this specific version is returned,
        otherwise the latest version is returned.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/way/{WayId}"
        if WayVersion != -1:
            uri += f"/{WayVersion}"
        data = self._session._get(uri)
        way = cast(Element, dom.OsmResponseToDom(data, tag="way", single=True))
        return dom.DomParseWay(way)

    def WayCreate(self, WayData: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Creates a way based on the supplied `WayData` dict:

            #!python
            {
                'nd': [] list of nodes,
                'tag': {} dict of tags,
            }

        Returns updated `WayData` (without timestamp):

            #!python
            {
                'id': id of node,
                'nd': [] list of nodes,
                'tag': {} dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of way,
                'user': username of last change,
                'uid': id of user of last change,
                'visible': True|False
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the supplied information contain an existing node,
        `OsmApi.OsmTypeAlreadyExistsError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("create", "way", WayData)

    def WayUpdate(self, WayData: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates way with the supplied `WayData` dict:

            #!python
            {
                'id': id of way,
                'nd': [] list of nodes,
                'tag': {},
                'version': version number of way,
            }

        Returns updated `WayData` (without timestamp):

            #!python
            {
                'id': id of node,
                'nd': [] list of nodes,
                'tag': {} dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of way,
                'user': username of last change,
                'uid': id of user of last change,
                'visible': True|False
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("modify", "way", WayData)

    def WayDelete(self, WayData: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Delete way with `WayData`:

            #!python
            {
                'id': id of way,
                'nd': [] list of nodes,
                'tag': dict of tags,
                'version': version number of way,
            }

        Returns updated `WayData` (without timestamp):

            #!python
            {
                'id': id of node,
                'nd': [] list of nodes,
                'tag': {} dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of way,
                'user': username of last change,
                'uid': id of user of last change,
                'visible': True|False
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.

        If the requested element has already been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        return self._do("delete", "way", WayData)

    def WayHistory(self, WayId: int) -> Dict[int, Dict[str, Any]]:
        """
        Returns dict with version as key:

            #!python
            {
                '1': dict of WayData,
                '2': dict of WayData,
                ...
            }

        `WayId` is the unique identifier of a way.
        """
        uri = f"/api/0.6/way/{WayId}/history"
        data = self._session._get(uri)
        ways = cast(List[Element], dom.OsmResponseToDom(data, tag="way"))
        result: Dict[int, Dict[str, Any]] = {}
        for way in ways:
            way_data = dom.DomParseWay(way)
            result[way_data["version"]] = way_data
        return result

    def WayRelations(self, WayId: int) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts of `RelationData` containing way `WayId`:

            #!python
            [
                {
                    'id': id of Relation,
                    'member': [
                        {
                            'ref': ID of referenced element,
                            'role': optional description of role in relation
                            'type': node|way|relation
                        },
                        {
                            ...
                        }
                    ]
                    'tag': {} dict of tags,
                    'changeset': id of changeset of last change,
                    'version': version number of Way,
                    'user': username of user that made the last change,
                    'uid': id of user that made the last change,
                    'visible': True|False
                },
                {
                    ...
                },
            ]

        The `WayId` is a unique identifier for a way.
        """
        uri = f"/api/0.6/way/{WayId}/relations"
        data = self._session._get(uri)
        relations = cast(
            List[Element], dom.OsmResponseToDom(data, tag="relation", allow_empty=True)
        )
        result: List[Dict[str, Any]] = []
        for relation in relations:
            relation_data = dom.DomParseRelation(relation)
            result.append(relation_data)
        return result

    def WayFull(self, WayId: int) -> List[Dict[str, Any]]:
        """
        Returns the full data for way `WayId` as list of dicts:

            #!python
            [
                {
                    'type': node|way|relation,
                    'data': {} data dict for node|way|relation
                },
                { ... }
            ]

        The `WayId` is a unique identifier for a way.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/way/{WayId}/full"
        data = self._session._get(uri)
        return parser.ParseOsm(data)

    def WaysGet(self, WayIdList: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Returns dict with the id of the way as a key for
        each way in `WayIdList`:

            #!python
            {
                '1234': dict of WayData,
                '5678': dict of WayData,
                ...
            }

        `WayIdList` is a list containing unique identifiers for multiple ways.
        """
        way_list = ",".join([str(x) for x in WayIdList])
        uri = f"/api/0.6/ways?ways={way_list}"
        data = self._session._get(uri)
        ways = cast(List[Element], dom.OsmResponseToDom(data, tag="way"))
        result: Dict[int, Dict[str, Any]] = {}
        for way in ways:
            way_data = dom.DomParseWay(way)
            result[way_data["id"]] = way_data
        return result

    ##################################################
    # Relation                                       #
    ##################################################

    def RelationGet(self, RelationId: int, RelationVersion: int = -1) -> Dict[str, Any]:
        """
        Returns relation with `RelationId` as a dict:

            #!python
            {
                'id': id of Relation,
                'member': [
                    {
                        'ref': ID of referenced element,
                        'role': optional description of role in relation
                        'type': node|way|relation
                    },
                    {
                        ...
                    }
                ]
                'tag': {} dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of Relation,
                'user': username of user that made the last change,
                'uid': id of user that made the last change,
                'timestamp': timestamp of last change,
                'visible': True|False
            }

        If `RelationVersion` is supplied, this specific version is returned,
        otherwise the latest version is returned.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/relation/{RelationId}"
        if RelationVersion != -1:
            uri += f"/{RelationVersion}"
        data = self._session._get(uri)
        relation = cast(
            Element, dom.OsmResponseToDom(data, tag="relation", single=True)
        )
        return dom.DomParseRelation(relation)

    def RelationCreate(self, RelationData: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Creates a relation based on the supplied `RelationData` dict:

            #!python
            {
                'member': [] list of members,
                'tag': {} dict of tags,
            }

        Returns updated `RelationData` (without timestamp):

            #!python
            {
                'id': id of Relation,
                'member': [
                    {
                        'ref': ID of referenced element,
                        'role': optional description of role in relation
                        'type': node|way|relation
                    },
                    {
                        ...
                    }
                ]
                'tag': {} dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of Relation,
                'user': username of user that made the last change,
                'uid': id of user that made the last change,
                'visible': True|False
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the supplied information contain an existing node,
        `OsmApi.OsmTypeAlreadyExistsError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("create", "relation", RelationData)

    def RelationUpdate(self, RelationData: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates relation with the supplied `RelationData` dict:

            #!python
            {
                'id': id of relation,
                'member': [] list of member dicts,
                'tag': {},
                'version': version number of relation,
            }

        Returns updated `RelationData` (without timestamp):

            #!python
            {
                'id': id of Relation,
                'member': [
                    {
                        'ref': ID of referenced element,
                        'role': optional description of role in relation
                        'type': node|way|relation
                    },
                    {
                        ...
                    }
                ]
                'tag': {} dict of tags
                'changeset': id of changeset of last change,
                'version': version number of Relation,
                'user': username of user that made the last change,
                'uid': id of user that made the last change,
                'visible': True|False
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("modify", "relation", RelationData)

    def RelationDelete(self, RelationData: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Delete relation with `RelationData` dict:

            #!python
            {
                'id': id of relation,
                'member': [] list of member dicts,
                'tag': {},
                'version': version number of relation,
            }

        Returns updated `RelationData` (without timestamp):

            #!python
            {
                'id': id of Relation,
                'member': [
                    {
                        'ref': ID of referenced element,
                        'role': optional description of role in relation
                        'type': node|way|relation
                    },
                    {
                        ...
                    }
                ]
                'tag': {} dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of Relation,
                'user': username of user that made the last change,
                'uid': id of user that made the last change,
                'visible': True|False
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.

        If the requested element has already been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        return self._do("delete", "relation", RelationData)

    def RelationHistory(self, RelationId: int) -> Dict[int, Dict[str, Any]]:
        """
        Returns dict with version as key:

            #!python
            {
                '1': dict of RelationData,
                '2': dict of RelationData,
                ...
            }

        `RelationId` is the unique identifier of a relation.
        """
        uri = f"/api/0.6/relation/{RelationId}/history"
        data = self._session._get(uri)
        relations = cast(List[Element], dom.OsmResponseToDom(data, tag="relation"))
        result: Dict[int, Dict[str, Any]] = {}
        for relation in relations:
            relation_data = dom.DomParseRelation(relation)
            result[relation_data["version"]] = relation_data
        return result

    def RelationRelations(self, RelationId: int) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts of `RelationData`
        containing relation `RelationId`:

            #!python
            [
                {
                    'id': id of Relation,
                    'member': [
                        {
                            'ref': ID of referenced element,
                            'role': optional description of role in relation
                            'type': node|way|relation
                        },
                        {
                            ...
                        }
                    ]
                    'tag': {} dict of tags,
                    'changeset': id of changeset of last change,
                    'version': version number of Way,
                    'user': username of user that made the last change,
                    'uid': id of user that made the last change,
                    'visible': True|False
                },
                {
                    ...
                },
            ]

        The `RelationId` is a unique identifier for a relation.
        """
        uri = f"/api/0.6/relation/{RelationId}/relations"
        data = self._session._get(uri)
        relations = cast(
            List[Element], dom.OsmResponseToDom(data, tag="relation", allow_empty=True)
        )
        result: List[Dict[str, Any]] = []
        for relation in relations:
            relation_data = dom.DomParseRelation(relation)
            result.append(relation_data)
        return result

    def RelationFullRecur(self, RelationId: int) -> List[Dict[str, Any]]:
        """
        Returns the full data (all levels) for relation
        `RelationId` as list of dicts:

            #!python
            [
                {
                    'type': node|way|relation,
                    'data': {} data dict for node|way|relation
                },
                { ... }
            ]

        The `RelationId` is a unique identifier for a way.

        This function is useful for relations containing other relations.

        If you don't need all levels, use `OsmApi.RelationFull`
        instead, which return only 2 levels.

        If any relation (on any level) has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        data = []
        todo = [RelationId]
        done = []
        while todo:
            rid = todo.pop(0)
            done.append(rid)
            temp = self.RelationFull(rid)
            for item in temp:
                if item["type"] != "relation":
                    continue
                if item["data"]["id"] in done:
                    continue
                todo.append(item["data"]["id"])
            data += temp
        return data

    def RelationFull(self, RelationId: int) -> List[Dict[str, Any]]:
        """
        Returns the full data (two levels) for relation
        `RelationId` as list of dicts:

            #!python
            [
                {
                    'type': node|way|relation,
                    'data': {} data dict for node|way|relation
                },
                { ... }
            ]

        The `RelationId` is a unique identifier for a way.

        If you need all levels, use `OsmApi.RelationFullRecur`.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/relation/{RelationId}/full"
        data = self._session._get(uri)
        return parser.ParseOsm(data)

    def RelationsGet(self, RelationIdList: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Returns dict with the id of the relation as a key
        for each relation in `RelationIdList`:

            #!python
            {
                '1234': dict of RelationData,
                '5678': dict of RelationData,
                ...
            }

        `RelationIdList` is a list containing unique identifiers
        for multiple relations.
        """
        relation_list = ",".join([str(x) for x in RelationIdList])
        uri = f"/api/0.6/relations?relations={relation_list}"
        data = self._session._get(uri)
        relations = cast(List[Element], dom.OsmResponseToDom(data, tag="relation"))
        result: Dict[int, Dict[str, Any]] = {}
        for relation in relations:
            relation_data = dom.DomParseRelation(relation)
            result[relation_data["id"]] = relation_data
        return result

    ##################################################
    # Changeset                                      #
    ##################################################

    @contextmanager
    def Changeset(self, ChangesetTags: Optional[Dict[str, str]] = None) -> Any:
        """
        Context manager for a Changeset.

        It opens a Changeset, uploads the changes and closes the changeset
        when used with the `with` statement:

            #!python
            import osmapi

            with osmapi.Changeset({"comment": "Import script XYZ"}) as changeset_id:
                print(f"Part of changeset {changeset_id}")
                api.NodeCreate({"lon":1, "lat":1, "tag": {}})

        If `ChangesetTags` are given, this tags are applied (key/value).

        Returns `ChangesetId`

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.
        """
        if ChangesetTags is None:
            ChangesetTags = {}
        # Create a new changeset
        changeset_id = self.ChangesetCreate(ChangesetTags)
        yield changeset_id

        # upload data to changeset
        autosize = self._changesetautosize
        for i in range(0, len(self._changesetautodata), autosize):
            chunk = self._changesetautodata[i : i + autosize]
            self.ChangesetUpload(chunk)
        self._changesetautodata = []
        self.ChangesetClose()

    def ChangesetGet(
        self, ChangesetId: int, include_discussion: bool = False
    ) -> Dict[str, Any]:
        """
        Returns changeset with `ChangesetId` as a dict:

            #!python
            {
                'id': id of Changeset,
                'open': True|False, wheter or not this changeset is open
                'tag': {} dict of tags,
                'created_at': timestamp of creation of this changeset
                'closed_at': timestamp when changeset was closed
                'comments_count': amount of comments
                'discussion': [] list of comment dict (-> `include_discussion`)
                'max_lon': maximum longitude of changes in this changeset
                'max_lat': maximum latitude of changes in this changeset
                'min_lon': minimum longitude of changes in this changeset
                'min_lat': minimum longitude of changes in this changeset
                'user': username of user that created this changeset,
                'uid': id of user that created this changeset,
            }

        `ChangesetId` is the unique identifier of a changeset.

        If `include_discussion` is set to `True` the changeset discussion
        will be available in the result.
        """
        path = f"/api/0.6/changeset/{ChangesetId}"
        if include_discussion:
            path = f"{path}?include_discussion=true"
        data = self._session._get(path)
        changeset = cast(
            Element, dom.OsmResponseToDom(data, tag="changeset", single=True)
        )
        return dom.DomParseChangeset(changeset, include_discussion=include_discussion)

    def ChangesetUpdate(self, ChangesetTags: Optional[Dict[str, str]] = None) -> int:
        """
        Updates current changeset with `ChangesetTags`.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        if ChangesetTags is None:
            ChangesetTags = {}
        if not self._CurrentChangesetId:
            raise errors.NoChangesetOpenError("No changeset currently opened")
        if "created_by" not in ChangesetTags:
            ChangesetTags["created_by"] = self._created_by
        try:
            self._session._put(
                f"/api/0.6/changeset/{self._CurrentChangesetId}",
                xmlbuilder._XmlBuild("changeset", {"tag": ChangesetTags}, data=self),
                return_value=False,
            )
        except errors.ApiError as e:
            if e.status == 409:
                raise errors.ChangesetClosedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise
        return self._CurrentChangesetId

    def ChangesetCreate(self, ChangesetTags: Optional[Dict[str, str]] = None) -> int:
        """
        Opens a changeset.

        If `ChangesetTags` are given, this tags are applied (key/value).

        Returns `ChangesetId`

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.
        """
        if ChangesetTags is None:
            ChangesetTags = {}
        if self._CurrentChangesetId:
            raise errors.ChangesetAlreadyOpenError("Changeset already opened")
        if "created_by" not in ChangesetTags:
            ChangesetTags["created_by"] = self._created_by

        # check if someone tries to create a test changeset to PROD
        if (
            self._api == "https://www.openstreetmap.org"
            and ChangesetTags.get("comment") == "My first test"
        ):
            raise errors.OsmApiError(
                "DO NOT CREATE test changesets on the production server"
            )

        result = self._session._put(
            "/api/0.6/changeset/create",
            xmlbuilder._XmlBuild("changeset", {"tag": ChangesetTags}, data=self),
        )
        self._CurrentChangesetId = int(result)
        return self._CurrentChangesetId

    def ChangesetClose(self) -> int:
        """
        Closes current changeset.

        Returns `ChangesetId`.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        if not self._CurrentChangesetId:
            raise errors.NoChangesetOpenError("No changeset currently opened")
        try:
            self._session._put(
                f"/api/0.6/changeset/{self._CurrentChangesetId}/close",
                None,
                return_value=False,
            )
            CurrentChangesetId = self._CurrentChangesetId
            self._CurrentChangesetId = 0
        except errors.ApiError as e:
            if e.status == 409:
                raise errors.ChangesetClosedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise
        return CurrentChangesetId

    def ChangesetUpload(
        self, ChangesData: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Upload data with the `ChangesData` list of dicts:

            #!python
            {
                type: node|way|relation,
                action: create|delete|modify,
                data: {}
            }

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
        for change in ChangesData:
            data += "<" + change["action"] + ">\n"
            changeData = change["data"]
            data += self._add_changeset_data(changeData, change["type"])
            data += "</" + change["action"] + ">\n"
        data += "</osmChange>"
        try:
            response_data = self._session._post(
                f"/api/0.6/changeset/{self._CurrentChangesetId}/upload",
                data.encode("utf-8"),
                forceAuth=True,
            )
        except errors.ApiError as e:
            if e.status == 409 and re.search(
                r"The changeset .* was closed at .*", e.payload
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

        for change in ChangesData:
            if change["action"] == "delete":
                for changeElement in change["data"]:
                    changeElement.pop("version")
            else:
                self._assign_id_and_version(result_elements, change["data"])

        return ChangesData

    def ChangesetDownload(self, ChangesetId: int) -> List[Dict[str, Any]]:
        """
        Download data from changeset `ChangesetId`.

        Returns list of dict:

            #!python
            {
                'type': node|way|relation,
                'action': create|delete|modify,
                'data': {}
            }
        """
        uri = f"/api/0.6/changeset/{ChangesetId}/download"
        data = self._session._get(uri)
        return parser.ParseOsc(data)

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
    ) -> Dict[int, Dict[str, Any]]:
        """
        Returns a dict with the id of the changeset as key
        matching all criteria:

            #!python
            {
                '1234': dict of ChangesetData,
                '5678': dict of ChangesetData,
                ...
            }

        All parameters are optional.
        """

        uri = "/api/0.6/changesets"
        params: Dict[str, Any] = {}
        if min_lon or min_lat or max_lon or max_lat:
            params["bbox"] = f"{min_lon},{min_lat},{max_lon},{max_lat}"
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
        changesets = cast(List[Element], dom.OsmResponseToDom(data, tag="changeset"))
        result: Dict[int, Dict[str, Any]] = {}
        for curChangeset in changesets:
            tmpCS = dom.DomParseChangeset(curChangeset)
            result[tmpCS["id"]] = tmpCS
        return result

    def ChangesetComment(self, ChangesetId: int, comment: str) -> Dict[str, Any]:
        """
        Adds a comment to the changeset `ChangesetId`

        `comment` should be a string.

        Returns the updated `ChangesetData` dict:

            #!python
            {
                'id': id of Changeset,
                'open': True|False, wheter or not this changeset is open
                'tag': {} dict of tags,
                'created_at': timestamp of creation of this changeset
                'closed_at': timestamp when changeset was closed
                'comments_count': amount of comments
                'max_lon': maximum longitude of changes in this changeset
                'max_lat': maximum latitude of changes in this changeset
                'min_lon': minimum longitude of changes in this changeset
                'min_lat': minimum longitude of changes in this changeset
                'user': username of user that created this changeset,
                'uid': id of user that created this changeset,
            }


        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        params = urllib.parse.urlencode({"text": comment})
        try:
            data = self._session._post(
                f"/api/0.6/changeset/{ChangesetId}/comment",
                params,  # type: ignore[arg-type]
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
            Element, dom.OsmResponseToDom(data, tag="changeset", single=True)
        )
        return dom.DomParseChangeset(changeset)

    def ChangesetSubscribe(self, ChangesetId: int) -> Dict[str, Any]:
        """
        Subcribe to the changeset discussion of changeset `ChangesetId`.

        The user will be informed about new comments (i.e. receive an email).

        Returns the updated `ChangesetData` dict:

            #!python
            {
                'id': id of Changeset,
                'open': True|False, wheter or not this changeset is open
                'tag': {} dict of tags,
                'created_at': timestamp of creation of this changeset
                'closed_at': timestamp when changeset was closed
                'comments_count': amount of comments
                'max_lon': maximum longitude of changes in this changeset
                'max_lat': maximum latitude of changes in this changeset
                'min_lon': minimum longitude of changes in this changeset
                'min_lat': minimum longitude of changes in this changeset
                'user': username of user that created this changeset,
                'uid': id of user that created this changeset,
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.
        """
        try:
            data = self._session._post(
                f"/api/0.6/changeset/{ChangesetId}/subscribe", None, forceAuth=True
            )
        except errors.ApiError as e:
            if e.status == 409:
                raise errors.AlreadySubscribedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise
        changeset = cast(
            Element, dom.OsmResponseToDom(data, tag="changeset", single=True)
        )
        return dom.DomParseChangeset(changeset)

    def ChangesetUnsubscribe(self, ChangesetId: int) -> Dict[str, Any]:
        """
        Subcribe to the changeset discussion of changeset `ChangesetId`.

        The user will be informed about new comments (i.e. receive an email).

        Returns the updated `ChangesetData` dict:

            #!python
            {
                'id': id of Changeset,
                'open': True|False, wheter or not this changeset is open
                'tag': {} dict of tags,
                'created_at': timestamp of creation of this changeset
                'closed_at': timestamp when changeset was closed
                'comments_count': amount of comments
                'max_lon': maximum longitude of changes in this changeset
                'max_lat': maximum latitude of changes in this changeset
                'min_lon': minimum longitude of changes in this changeset
                'min_lat': minimum longitude of changes in this changeset
                'user': username of user that created this changeset,
                'uid': id of user that created this changeset,
            }

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.
        """
        try:
            data = self._session._post(
                f"/api/0.6/changeset/{ChangesetId}/unsubscribe", None, forceAuth=True
            )
        except errors.ElementNotFoundApiError as e:
            raise errors.NotSubscribedApiError(e.status, e.reason, e.payload) from e

        changeset = cast(
            Element, dom.OsmResponseToDom(data, tag="changeset", single=True)
        )
        return dom.DomParseChangeset(changeset)

    ##################################################
    # Notes                                          #
    ##################################################

    def NotesGet(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        limit: int = 100,
        closed: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts of notes in the specified bounding box:

            #!python
            [
                {
                    'id': integer,
                    'action': opened|commented|closed,
                    'status': open|closed
                    'date_created': creation date
                    'date_closed': closing data|None
                    'uid': User ID|None
                    'user': User name|None
                    'comments': {}
                },
                { ... }
            ]

        The limit parameter defines how many results should be returned.

        closed specifies the number of days a bug needs to be closed
        to no longer be returned.
        The value 0 means only open bugs are returned,
        -1 means all bugs are returned.

        All parameters are optional.
        """
        uri = (
            f"/api/0.6/notes?bbox="
            f"{min_lon:f},{min_lat:f},{max_lon:f},{max_lat:f}"
            f"&limit={limit}&closed={closed}"
        )
        data = self._session._get(uri)
        return parser.ParseNotes(data)

    def NoteGet(self, id: int) -> Dict[str, Any]:
        """
        Returns a note as dict:

            #!python
            {
                'id': integer,
                'action': opened|commented|closed,
                'status': open|closed
                'date_created': creation date
                'date_closed': closing data|None
                'uid': User ID|None
                'user': User name|None
                'comments': {}
            }

        `id` is the unique identifier of the note.
        """
        uri = f"/api/0.6/notes/{id}"
        data = self._session._get(uri)
        noteElement = cast(Element, dom.OsmResponseToDom(data, tag="note", single=True))
        return dom.DomParseNote(noteElement)

    def NoteCreate(self, NoteData: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a note based on the supplied `NoteData` dict:

            #!python
            {
                'lat': latitude of note,
                'lon': longitude of note,
                'text': text of the note,
            }

        Returns updated `NoteData`:

            #!python
            {
                'id': id of note,
                'lat': latitude of note,
                'lon': longitude of note,
                'date_created': date when the note was created
                'date_closed': date when the note was closed or None if it's open,
                'status': status of the note (open or closed),
                'comments': [
                    {
                        'date': date of the comment,
                        'action': status of comment (opened, commented, closed),
                        'text': text of the note,
                        'html': html version of the text of the note,
                        'uid': user id of the user creating this note or None
                        'user': username of the user creating this note or None
                    }
                ]
            }

        """
        uri = "/api/0.6/notes"
        uri += "?" + urllib.parse.urlencode(NoteData)
        return self._NoteAction(uri)

    def NoteComment(self, NoteId: int, comment: str) -> Dict[str, Any]:
        """
        Adds a new comment to a note.

        Returns the updated note.
        """
        path = f"/api/0.6/notes/{NoteId}/comment"
        return self._NoteAction(path, comment)

    def NoteClose(self, NoteId: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Closes a note.

        Returns the updated note.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.
        """
        path = f"/api/0.6/notes/{NoteId}/close"
        return self._NoteAction(path, comment, optionalAuth=False)

    def NoteReopen(self, NoteId: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Reopens a note.

        Returns the updated note.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        path = f"/api/0.6/notes/{NoteId}/reopen"
        return self._NoteAction(path, comment, optionalAuth=False)

    def NotesSearch(
        self, query: str, limit: int = 100, closed: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts of notes that match the given search query.

        The limit parameter defines how many results should be returned.

        closed specifies the number of days a bug needs to be closed
        to no longer be returned.
        The value 0 means only open bugs are returned,
        -1 means all bugs are returned.
        """
        uri = "/api/0.6/notes/search"
        params: Dict[str, Any] = {}
        params["q"] = query
        params["limit"] = limit
        params["closed"] = closed
        uri += "?" + urllib.parse.urlencode(params)
        data = self._session._get(uri)

        return parser.ParseNotes(data)

    def _NoteAction(
        self, path: str, comment: Optional[str] = None, optionalAuth: bool = True
    ) -> Dict[str, Any]:
        """
        Performs an action on a Note with a comment

        Return the updated note
        """
        uri = path
        if comment is not None:
            params = {}
            params["text"] = comment
            uri += "?" + urllib.parse.urlencode(params)
        try:
            result = self._session._post(uri, None, optionalAuth=optionalAuth)
        except errors.ApiError as e:
            if e.status == 409:
                raise errors.NoteAlreadyClosedApiError(
                    e.status, e.reason, e.payload
                ) from e
            else:
                raise

        # parse the result
        noteElement = cast(
            Element, dom.OsmResponseToDom(result, tag="note", single=True)
        )
        return dom.DomParseNote(noteElement)

    ##################################################
    # Other                                          #
    ##################################################

    def Map(
        self, min_lon: float, min_lat: float, max_lon: float, max_lat: float
    ) -> List[Dict[str, Any]]:
        """
        Download data in bounding box.

        Returns list of dict:

            #!python
            {
                type: node|way|relation,
                data: {}
            }
        """
        uri = f"/api/0.6/map?bbox={min_lon:f},{min_lat:f},{max_lon:f},{max_lat:f}"
        data = self._session._get(uri)
        return parser.ParseOsm(data)

    def flush(self) -> None:
        """
        Force the changes to be uploaded to OSM and the changeset to be closed

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.
        """
        return self._changesetautoflush(True)

    ##################################################
    # Internal method                                #
    ##################################################

    def _do(
        self, action: str, OsmType: str, OsmData: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if self._changesetauto:
            self._changesetautodata.append(
                {"action": action, "type": OsmType, "data": OsmData}
            )
            self._changesetautoflush()
            return None
        else:
            return self._do_manu(action, OsmType, OsmData)

    def _do_manu(  # type: ignore[return-value]
        self, action: str, OsmType: str, OsmData: Dict[str, Any]
    ) -> Dict[str, Any]:  # noqa
        if not self._CurrentChangesetId:
            raise errors.NoChangesetOpenError(
                "You need to open a changeset before uploading data"
            )
        if "timestamp" in OsmData:
            OsmData.pop("timestamp")
        OsmData["changeset"] = self._CurrentChangesetId
        if action == "create":
            if OsmData.get("id", -1) > 0:
                raise errors.OsmTypeAlreadyExistsError(f"This {OsmType} already exists")
            try:
                result = self._session._put(
                    f"/api/0.6/{OsmType}/create",
                    xmlbuilder._XmlBuild(OsmType, OsmData, data=self),
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
            OsmData["id"] = int(result.strip())
            OsmData["version"] = 1
            return OsmData
        elif action == "modify":
            try:
                result = self._session._put(
                    f"/api/0.6/{OsmType}/{OsmData['id']}",
                    xmlbuilder._XmlBuild(OsmType, OsmData, data=self),
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
            OsmData["version"] = int(result.strip())
            return OsmData
        elif action == "delete":
            try:
                result = self._session._delete(
                    f"/api/0.6/{OsmType}/{OsmData['id']}",
                    xmlbuilder._XmlBuild(OsmType, OsmData, data=self),
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
            OsmData["version"] = int(result.strip())
            OsmData["visible"] = False
            return OsmData

    def _changesetautoflush(self, force: bool = False) -> None:
        autosize = self._changesetautosize
        while (len(self._changesetautodata) >= autosize) or (
            force and self._changesetautodata
        ):
            if self._changesetautocpt == 0:
                self.ChangesetCreate(self._changesetautotags)
            self.ChangesetUpload(self._changesetautodata[:autosize])
            self._changesetautodata = self._changesetautodata[autosize:]
            self._changesetautocpt += 1
            if self._changesetautocpt == self._changesetautomulti:
                self.ChangesetClose()
                self._changesetautocpt = 0
        if self._changesetautocpt and force:
            self.ChangesetClose()
            self._changesetautocpt = 0
        return None

    def _add_changeset_data(self, changeData: List[Dict[str, Any]], type: str) -> str:
        data = ""
        for changedElement in changeData:
            changedElement["changeset"] = self._CurrentChangesetId
            data += xmlbuilder._XmlBuild(type, changedElement, False, data=self).decode(
                "utf-8"
            )
        return data

    def _assign_id_and_version(
        self, ResponseData: List[Element], RequestData: List[Dict[str, Any]]
    ) -> None:
        for response, element in zip(ResponseData, RequestData):
            element["id"] = int(response.getAttribute("new_id"))
            element["version"] = int(response.getAttribute("new_version"))
