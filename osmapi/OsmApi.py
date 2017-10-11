# -*- coding: utf-8 -*-

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

from __future__ import (absolute_import, print_function, unicode_literals)
import xml.dom.minidom
import xml.parsers.expat
import time
import sys
import urllib
import requests
from datetime import datetime

from osmapi import __version__

# Python 3.x
if getattr(urllib, 'urlencode', None) is None:
    urllib.urlencode = urllib.parse.urlencode


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


class OsmApi:
    """
    Main class of osmapi, instanciate this class to use osmapi
    """

    MAX_RETRY_LIMIT = 5
    """Maximum retries if a call to the remote API fails (default: 5)"""

    def __init__(
            self,
            username=None,
            password=None,
            passwordfile=None,
            appid="",
            created_by="osmapi/%s" % __version__,
            api="https://www.openstreetmap.org",
            changesetauto=False,
            changesetautotags={},
            changesetautosize=500,
            changesetautomulti=1,
            debug=False):
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

        The `debug` parameter can be used to generate a more verbose output.
        """

        # debug
        self._debug = debug

        # Get username
        if username:
            self._username = username
        elif passwordfile:
            pass_line = open(passwordfile).readline()
            self._username = pass_line.split(":")[0].strip()

        # Get password
        if password:
            self._password = password
        elif passwordfile:
            for l in open(passwordfile).readlines():
                l = l.strip().split(":")
                if l[0] == self._username:
                    self._password = l[1]

        # Changest informations
        # auto create and close changesets
        self._changesetauto = changesetauto
        # tags for automatic created changesets
        self._changesetautotags = changesetautotags
        # change count for auto changeset
        self._changesetautosize = changesetautosize
        # change count for auto changeset
        self._changesetautosize = changesetautosize
        # close a changeset every # upload
        self._changesetautomulti = changesetautomulti
        self._changesetautocpt = 0
        # data to upload for auto group
        self._changesetautodata = []

        # Get API
        self._api = api.strip('/')

        # Get created_by
        if not appid:
            self._created_by = created_by
        else:
            self._created_by = "%s (%s)" % (appid, created_by)

        # Initialisation
        self._CurrentChangesetId = 0

        # Http connection
        self._session = self._get_http_session()

    def __del__(self):
        try:
            if self._changesetauto:
                self._changesetautoflush(True)
        except ResponseEmptyApiError:
            pass

        return None

    ##################################################
    # Capabilities                                   #
    ##################################################

    def Capabilities(self):
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
        data = self._get(uri)

        data = self._OsmResponseToDom(data, tag="api", single=True)
        result = {}
        for elem in data.childNodes:
            if elem.nodeType != elem.ELEMENT_NODE:
                continue
            result[elem.nodeName] = {}
            for k, v in elem.attributes.items():
                try:
                    result[elem.nodeName][k] = float(v)
                except:
                    result[elem.nodeName][k] = v
        return result

    ##################################################
    # Node                                           #
    ##################################################

    def NodeGet(self, NodeId, NodeVersion=-1):
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
        """
        uri = "/api/0.6/node/%s" % (NodeId)
        if NodeVersion != -1:
            uri += "/%s" % (NodeVersion)
        data = self._get(uri)
        data = self._OsmResponseToDom(data, tag="node", single=True)
        return self._DomParseNode(data)

    def NodeCreate(self, NodeData):
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
        """
        return self._do("create", "node", NodeData)

    def NodeUpdate(self, NodeData):
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
        """
        return self._do("modify", "node", NodeData)

    def NodeDelete(self, NodeData):
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

        If the requested element has already been deleted,
        `OsmApi.ElementDeletedApiError` is raised.
        """
        return self._do("delete", "node", NodeData)

    def NodeHistory(self, NodeId):
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
        uri = "/api/0.6/node/%s/history" % NodeId
        data = self._get(uri)
        nodes = self._OsmResponseToDom(data, tag="node")
        result = {}
        for node in nodes:
            data = self._DomParseNode(node)
            result[data["version"]] = data
        return result

    def NodeWays(self, NodeId):
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
        uri = "/api/0.6/node/%d/ways" % NodeId
        data = self._get(uri)
        ways = self._OsmResponseToDom(data, tag="way")
        result = []
        for way in ways:
            data = self._DomParseWay(way)
            result.append(data)
        return result

    def NodeRelations(self, NodeId):
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
        uri = "/api/0.6/node/%d/relations" % NodeId
        data = self._get(uri)
        relations = self._OsmResponseToDom(data, tag="relation")
        result = []
        for relation in relations:
            data = self._DomParseRelation(relation)
            result.append(data)
        return result

    def NodesGet(self, NodeIdList):
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
        uri = "/api/0.6/nodes?nodes=%s" % node_list
        data = self._get(uri)
        nodes = self._OsmResponseToDom(data, tag="node")
        result = {}
        for node in nodes:
            data = self._DomParseNode(node)
            result[data["id"]] = data
        return result

    ##################################################
    # Way                                            #
    ##################################################

    def WayGet(self, WayId, WayVersion=-1):
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
        """
        uri = "/api/0.6/way/%s" % (WayId)
        if WayVersion != -1:
            uri += "/%s" % (WayVersion)
        data = self._get(uri)
        way = self._OsmResponseToDom(data, tag="way", single=True)
        return self._DomParseWay(way)

    def WayCreate(self, WayData):
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
        """
        return self._do("create", "way", WayData)

    def WayUpdate(self, WayData):
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
        """
        return self._do("modify", "way", WayData)

    def WayDelete(self, WayData):
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

        If the requested element has already been deleted,
        `OsmApi.ElementDeletedApiError` is raised.
        """
        return self._do("delete", "way", WayData)

    def WayHistory(self, WayId):
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
        uri = "/api/0.6/way/%s/history" % (WayId)
        data = self._get(uri)
        ways = self._OsmResponseToDom(data, tag="way")
        result = {}
        for way in ways:
            data = self._DomParseWay(way)
            result[data["version"]] = data
        return result

    def WayRelations(self, WayId):
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
        uri = "/api/0.6/way/%d/relations" % WayId
        data = self._get(uri)
        relations = self._OsmResponseToDom(data, tag="relation")
        result = []
        for relation in relations:
            data = self._DomParseRelation(relation)
            result.append(data)
        return result

    def WayFull(self, WayId):
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
        """
        uri = "/api/0.6/way/%s/full" % (WayId)
        data = self._get(uri)
        return self.ParseOsm(data)

    def WaysGet(self, WayIdList):
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
        uri = "/api/0.6/ways?ways=%s" % way_list
        data = self._get(uri)
        ways = self._OsmResponseToDom(data, tag="way")
        result = {}
        for way in ways:
            data = self._DomParseWay(way)
            result[data["id"]] = data
        return result

    ##################################################
    # Relation                                       #
    ##################################################

    def RelationGet(self, RelationId, RelationVersion=-1):
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
        """
        uri = "/api/0.6/relation/%s" % (RelationId)
        if RelationVersion != -1:
            uri += "/%s" % (RelationVersion)
        data = self._get(uri)
        relation = self._OsmResponseToDom(data, tag="relation", single=True)
        return self._DomParseRelation(relation)

    def RelationCreate(self, RelationData):
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
        """
        return self._do("create", "relation", RelationData)

    def RelationUpdate(self, RelationData):
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
        """
        return self._do("modify", "relation", RelationData)

    def RelationDelete(self, RelationData):
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

        If the requested element has already been deleted,
        `OsmApi.ElementDeletedApiError` is raised.
        """
        return self._do("delete", "relation", RelationData)

    def RelationHistory(self, RelationId):
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
        uri = "/api/0.6/relation/%s/history" % (RelationId)
        data = self._get(uri)
        relations = self._OsmResponseToDom(data, tag="relation")
        result = {}
        for relation in relations:
            data = self._DomParseRelation(relation)
            result[data["version"]] = data
        return result

    def RelationRelations(self, RelationId):
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
        uri = "/api/0.6/relation/%d/relations" % RelationId
        data = self._get(uri)
        relations = self._OsmResponseToDom(data, tag="relation")
        result = []
        for relation in relations:
            data = self._DomParseRelation(relation)
            result.append(data)
        return result

    def RelationFullRecur(self, RelationId):
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

    def RelationFull(self, RelationId):
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
        """
        uri = "/api/0.6/relation/%s/full" % (RelationId)
        data = self._get(uri)
        return self.ParseOsm(data)

    def RelationsGet(self, RelationIdList):
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
        uri = "/api/0.6/relations?relations=%s" % relation_list
        data = self._get(uri)
        relations = self._OsmResponseToDom(data, tag="relation")
        result = {}
        for relation in relations:
            data = self._DomParseRelation(relation)
            result[data["id"]] = data
        return result

    ##################################################
    # Changeset                                      #
    ##################################################

    def ChangesetGet(self, ChangesetId, include_discussion=False):
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
        path = "/api/0.6/changeset/%s" % (ChangesetId)
        if (include_discussion):
            path += "?include_discussion=true"
        data = self._get(path)
        changeset = self._OsmResponseToDom(data, tag="changeset", single=True)
        return self._DomParseChangeset(changeset)

    def ChangesetUpdate(self, ChangesetTags={}):
        """
        Updates current changeset with `ChangesetTags`.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.
        """
        if not self._CurrentChangesetId:
            raise NoChangesetOpenError("No changeset currently opened")
        if "created_by" not in ChangesetTags:
            ChangesetTags["created_by"] = self._created_by
        self._put(
            "/api/0.6/changeset/%s" % (self._CurrentChangesetId),
            self._XmlBuild("changeset", {"tag": ChangesetTags}),
            return_value=False
        )
        return self._CurrentChangesetId

    def ChangesetCreate(self, ChangesetTags={}):
        """
        Opens a changeset.

        If `ChangesetTags` are given, this tags are applied (key/value).

        Returns `ChangesetId`

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.
        """
        if self._CurrentChangesetId:
            raise ChangesetAlreadyOpenError("Changeset already opened")
        if "created_by" not in ChangesetTags:
            ChangesetTags["created_by"] = self._created_by
        result = self._put(
            "/api/0.6/changeset/create",
            self._XmlBuild("changeset", {"tag": ChangesetTags})
        )
        self._CurrentChangesetId = int(result)
        return self._CurrentChangesetId

    def ChangesetClose(self):
        """
        Closes current changeset.

        Returns `ChangesetId`.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.
        """
        if not self._CurrentChangesetId:
            raise NoChangesetOpenError("No changeset currently opened")
        self._put(
            "/api/0.6/changeset/%s/close" % (self._CurrentChangesetId),
            "",
            return_value=False
        )
        CurrentChangesetId = self._CurrentChangesetId
        self._CurrentChangesetId = 0
        return CurrentChangesetId

    def ChangesetUpload(self, ChangesData):
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
        """
        data = ""
        data += "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        data += "<osmChange version=\"0.6\" generator=\""
        data += self._created_by + "\">\n"
        for change in ChangesData:
            data += "<" + change["action"] + ">\n"
            change["data"]["changeset"] = self._CurrentChangesetId
            data += self._XmlBuild(
                change["type"],
                change["data"],
                False
            ).decode("utf-8")
            data += "</" + change["action"] + ">\n"
        data += "</osmChange>"
        data = self._post(
            "/api/0.6/changeset/%s/upload" % (self._CurrentChangesetId),
            data.encode("utf-8")
        )
        try:
            data = xml.dom.minidom.parseString(data)
            data = data.getElementsByTagName("diffResult")[0]
            data = [x for x in data.childNodes if x.nodeType == x.ELEMENT_NODE]
        except (xml.parsers.expat.ExpatError, IndexError) as e:
            raise XmlResponseInvalidError(
                "The XML response from the OSM API is invalid: %r" % e
            )

        for i in range(len(ChangesData)):
            if ChangesData[i]["action"] == "delete":
                ChangesData[i]["data"].pop("version")
            else:
                new_id = int(data[i].getAttribute("new_id"))
                ChangesData[i]["data"]["id"] = new_id
                new_version = int(data[i].getAttribute("new_version"))
                ChangesData[i]["data"]["version"] = new_version
        return ChangesData

    def ChangesetDownload(self, ChangesetId):
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
        uri = "/api/0.6/changeset/%s/download" % (ChangesetId)
        data = self._get(uri)
        return self.ParseOsc(data)

    def ChangesetsGet(  # noqa
            self,
            min_lon=None,
            min_lat=None,
            max_lon=None,
            max_lat=None,
            userid=None,
            username=None,
            closed_after=None,
            created_before=None,
            only_open=False,
            only_closed=False):
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
        params = {}
        if min_lon or min_lat or max_lon or max_lat:
            params["bbox"] = ",".join(
                [
                    str(min_lon),
                    str(min_lat),
                    str(max_lon),
                    str(max_lat)
                ]
            )
        if userid:
            params["user"] = userid
        if username:
            params["display_name"] = username
        if closed_after and not created_before:
            params["time"] = closed_after
        if created_before:
            if not closed_after:
                closed_after = "1970-01-01T00:00:00Z"
            params["time"] = "%s,%s" % (closed_after, created_before)
        if only_open:
            params["open"] = 1
        if only_closed:
            params["closed"] = 1

        if params:
            uri += "?" + urllib.urlencode(params)

        data = self._get(uri)
        changesets = self._OsmResponseToDom(data, tag="changeset")
        result = {}
        for curChangeset in changesets:
            tmpCS = self._DomParseChangeset(curChangeset)
            result[tmpCS["id"]] = tmpCS
        return result

    def ChangesetComment(self, ChangesetId, comment):
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
        """
        params = urllib.urlencode({'text': comment})
        data = self._post(
            "/api/0.6/changeset/%s/comment" % (ChangesetId),
            params
        )
        changeset = self._OsmResponseToDom(data, tag="changeset", single=True)
        return self._DomParseChangeset(changeset)

    def ChangesetSubscribe(self, ChangesetId):
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
            data = self._post(
                "/api/0.6/changeset/%s/subscribe" % (ChangesetId),
                None
            )
        except ApiError as e:
            if e.status == 409:
                raise AlreadySubscribedApiError(e.status, e.reason, e.payload)
            else:
                raise
        changeset = self._OsmResponseToDom(data, tag="changeset", single=True)
        return self._DomParseChangeset(changeset)

    def ChangesetUnsubscribe(self, ChangesetId):
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
            data = self._post(
                "/api/0.6/changeset/%s/unsubscribe" % (ChangesetId),
                None
            )
        except ApiError as e:
            if e.status == 404:
                raise NotSubscribedApiError(e.status, e.reason, e.payload)
            else:
                raise
        changeset = self._OsmResponseToDom(data, tag="changeset", single=True)
        return self._DomParseChangeset(changeset)

    ##################################################
    # Notes                                          #
    ##################################################

    def NotesGet(
            self,
            min_lon,
            min_lat,
            max_lon,
            max_lat,
            limit=100,
            closed=7):
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
            "/api/0.6/notes?bbox=%f,%f,%f,%f&limit=%d&closed=%d"
            % (min_lon, min_lat, max_lon, max_lat, limit, closed)
        )
        data = self._get(uri)
        return self.ParseNotes(data)

    def NoteGet(self, id):
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
        uri = "/api/0.6/notes/%s" % (id)
        data = self._get(uri)
        noteElement = self._OsmResponseToDom(data, tag="note", single=True)
        return self._DomParseNote(noteElement)

    def NoteCreate(self, NoteData):
        """
        Creates a note.

        Returns updated NoteData (without timestamp).
        """
        uri = "/api/0.6/notes"
        uri += "?" + urllib.urlencode(NoteData)
        return self._NoteAction(uri)

    def NoteComment(self, NoteId, comment):
        """
        Adds a new comment to a note.

        Returns the updated note.
        """
        path = "/api/0.6/notes/%s/comment" % NoteId
        return self._NoteAction(path, comment)

    def NoteClose(self, NoteId, comment):
        """
        Closes a note.

        Returns the updated note.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.
        """
        path = "/api/0.6/notes/%s/close" % NoteId
        return self._NoteAction(path, comment, optionalAuth=False)

    def NoteReopen(self, NoteId, comment):
        """
        Reopens a note.

        Returns the updated note.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.
        """
        path = "/api/0.6/notes/%s/reopen" % NoteId
        return self._NoteAction(path, comment, optionalAuth=False)

    def NotesSearch(self, query, limit=100, closed=7):
        """
        Returns a list of dicts of notes that match the given search query.

        The limit parameter defines how many results should be returned.

        closed specifies the number of days a bug needs to be closed
        to no longer be returned.
        The value 0 means only open bugs are returned,
        -1 means all bugs are returned.
        """
        uri = "/api/0.6/notes/search"
        params = {}
        params['q'] = query
        params['limit'] = limit
        params['closed'] = closed
        uri += "?" + urllib.urlencode(params)
        data = self._get(uri)

        return self.ParseNotes(data)

    def _NoteAction(self, path, comment=None, optionalAuth=True):
        """
        Performs an action on a Note with a comment

        Return the updated note
        """
        uri = path
        if comment is not None:
            params = {}
            params['text'] = comment
            uri += "?" + urllib.urlencode(params)
        result = self._post(uri, None, optionalAuth=optionalAuth)

        # parse the result
        noteElement = self._OsmResponseToDom(result, tag="note", single=True)
        return self._DomParseNote(noteElement)

    ##################################################
    # Other                                          #
    ##################################################

    def Map(self, min_lon, min_lat, max_lon, max_lat):
        """
        Download data in bounding box.

        Returns list of dict:

            #!python
            {
                type: node|way|relation,
                data: {}
            }
        """
        uri = (
            "/api/0.6/map?bbox=%f,%f,%f,%f"
            % (min_lon, min_lat, max_lon, max_lat)
        )
        data = self._get(uri)
        return self.ParseOsm(data)

    ##################################################
    # Data parser                                    #
    ##################################################

    def ParseOsm(self, data):
        """
        Parse osm data.

        Returns list of dict:

            #!python
            {
                type: node|way|relation,
                data: {}
            }
        """
        try:
            data = xml.dom.minidom.parseString(data)
            data = data.getElementsByTagName("osm")[0]
        except (xml.parsers.expat.ExpatError, IndexError) as e:
            raise XmlResponseInvalidError(
                "The XML response from the OSM API is invalid: %r" % e
            )

        result = []
        for elem in data.childNodes:
            if elem.nodeName == "node":
                result.append({
                    "type": elem.nodeName,
                    "data": self._DomParseNode(elem)
                })
            elif elem.nodeName == "way":
                result.append({
                    "type": elem.nodeName,
                    "data": self._DomParseWay(elem)
                })
            elif elem.nodeName == "relation":
                result.append({
                    "type": elem.nodeName,
                    "data": self._DomParseRelation(elem)
                })
        return result

    def ParseOsc(self, data):
        """
        Parse osc data.

        Returns list of dict:

            #!python
            {
                type: node|way|relation,
                action: create|delete|modify,
                data: {}
            }
        """
        try:
            data = xml.dom.minidom.parseString(data)
            data = data.getElementsByTagName("osmChange")[0]
        except (xml.parsers.expat.ExpatError, IndexError) as e:
            raise XmlResponseInvalidError(
                "The XML response from the OSM API is invalid: %r" % e
            )

        result = []
        for action in data.childNodes:
            if action.nodeName == "#text":
                continue
            for elem in action.childNodes:
                if elem.nodeName == "node":
                    result.append({
                        "action": action.nodeName,
                        "type": elem.nodeName,
                        "data": self._DomParseNode(elem)
                    })
                elif elem.nodeName == "way":
                    result.append({
                        "action": action.nodeName,
                        "type": elem.nodeName,
                        "data": self._DomParseWay(elem)
                    })
                elif elem.nodeName == "relation":
                    result.append({
                        "action": action.nodeName,
                        "type": elem.nodeName,
                        "data": self._DomParseRelation(elem)
                    })
        return result

    def ParseNotes(self, data):
        """
        Parse notes data.

        Returns a list of dict:

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
        """
        noteElements = self._OsmResponseToDom(data, tag="note")
        result = []
        for noteElement in noteElements:
            note = self._DomParseNote(noteElement)
            result.append(note)
        return result

    ##################################################
    # Internal http function                         #
    ##################################################

    def _do(self, action, OsmType, OsmData):
        if self._changesetauto:
            self._changesetautodata.append({
                "action": action,
                "type": OsmType,
                "data": OsmData
            })
            self._changesetautoflush()
            return None
        else:
            return self._do_manu(action, OsmType, OsmData)

    def _do_manu(self, action, OsmType, OsmData):
        if not self._CurrentChangesetId:
            raise NoChangesetOpenError(
                "You need to open a changeset before uploading data"
            )
        if "timestamp" in OsmData:
            OsmData.pop("timestamp")
        OsmData["changeset"] = self._CurrentChangesetId
        if action == "create":
            if OsmData.get("id", -1) > 0:
                raise OsmTypeAlreadyExistsError(
                    "This %s already exists" % OsmType
                )
            result = self._put(
                "/api/0.6/%s/create" % OsmType,
                self._XmlBuild(OsmType, OsmData)
            )
            OsmData["id"] = int(result.strip())
            OsmData["version"] = 1
            return OsmData
        elif action == "modify":
            result = self._put(
                "/api/0.6/%s/%s" % (OsmType, OsmData["id"]),
                self._XmlBuild(OsmType, OsmData)
            )
            OsmData["version"] = int(result.strip())
            return OsmData
        elif action == "delete":
            result = self._delete(
                "/api/0.6/%s/%s" % (OsmType, OsmData["id"]),
                self._XmlBuild(OsmType, OsmData)
            )
            OsmData["version"] = int(result.strip())
            OsmData["visible"] = False
            return OsmData

    def flush(self):
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

    def _changesetautoflush(self, force=False):
        autosize = self._changesetautosize
        while ((len(self._changesetautodata) >= autosize) or
                (force and self._changesetautodata)):
            if self._changesetautocpt == 0:
                self.ChangesetCreate(self._changesetautotags)
            self.ChangesetUpload(
                self._changesetautodata[:autosize]
            )
            self._changesetautodata = self._changesetautodata[autosize:]
            self._changesetautocpt += 1
            if self._changesetautocpt == self._changesetautomulti:
                self.ChangesetClose()
                self._changesetautocpt = 0
        if self._changesetautocpt and force:
            self.ChangesetClose()
            self._changesetautocpt = 0
        return None

    def _http_request(self, method, path, auth, send, return_value=True):  # noqa
        """
        Returns the response generated by an HTTP request.

        `method` is a HTTP method to be executed
        with the request data. For example: 'GET' or 'POST'.
        `path` is the path to the requested resource relative to the
        base API address stored in self._api. Should start with a
        slash character to separate the URL.
        `auth` is a boolean indicating whether authentication should
        be preformed on this request.
        `send` contains additional data that might be sent in a
        request.
        `return_value` indicates wheter this request should return
        any data or not.

        If the username or password is missing,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the response status code indicates an error,
        `OsmApi.ApiError` is raised.
        """
        if self._debug:
            error_msg = (
                "%s %s %s"
                % (time.strftime("%Y-%m-%d %H:%M:%S"), method, path)
            )
            print(error_msg, file=sys.stderr)

        # Add API base URL to path
        path = self._api + path

        user_pass = None
        if auth:
            try:
                user_pass = (self._username, self._password)
            except AttributeError:
                raise UsernamePasswordMissingError("Username/Password missing")

        response = self._session.request(method, path, auth=user_pass,
                                         data=send)
        if response.status_code != 200:
            payload = response.content.strip()
            if response.status_code == 410:
                raise ElementDeletedApiError(
                    response.status_code,
                    response.reason,
                    payload
                )
            raise ApiError(response.status_code, response.reason, payload)
        if return_value and not response.content:
            raise ResponseEmptyApiError(
                response.status_code,
                response.reason,
                ''
            )

        if self._debug:
            error_msg = (
                "%s %s %s"
                % (time.strftime("%Y-%m-%d %H:%M:%S"), method, path)
            )
            print(error_msg, file=sys.stderr)
        return response.content

    def _http(self, cmd, path, auth, send, return_value=True):  # noqa
        i = 0
        while True:
            i += 1
            try:
                return self._http_request(
                    cmd,
                    path,
                    auth,
                    send,
                    return_value=return_value
                )
            except ApiError as e:
                if e.status >= 500:
                    if i == self.MAX_RETRY_LIMIT:
                        raise
                    if i != 1:
                        self._sleep()
                    self._session = self._get_http_session()
                else:
                    raise
            except Exception as e:
                print(e)
                if i == self.MAX_RETRY_LIMIT:
                    if isinstance(e, OsmApiError):
                        raise
                    raise MaximumRetryLimitReachedError(
                        "Give up after %s retries" % i
                    )
                if i != 1:
                    self._sleep()
                self._session = self._get_http_session()

    def _get_http_session(self):
        """
        Creates a requests session for connection pooling.
        """
        session = requests.Session()
        session.headers.update({
            'user-agent': self._created_by
        })
        return session

    def _sleep(self):
        time.sleep(5)

    def _get(self, path):
        return self._http('GET', path, False, None)

    def _put(self, path, data, return_value=True):
        return self._http('PUT', path, True, data, return_value=return_value)

    def _post(self, path, data, optionalAuth=False):
        auth = True
        # the Notes API allows certain POSTs by non-authenticated users
        if optionalAuth:
            auth = hasattr(self, '_username')
        return self._http('POST', path, auth, data)

    def _delete(self, path, data):
        return self._http('DELETE', path, True, data)

    ##################################################
    # Internal dom function                          #
    ##################################################

    def _OsmResponseToDom(self, response, tag, single=False):
        """
        Returns the (sub-) DOM parsed from an OSM response
        """
        try:
            dom = xml.dom.minidom.parseString(response)
            osm_dom = dom.getElementsByTagName("osm")[0]
            all_data = osm_dom.getElementsByTagName(tag)
            first_element = all_data[0]
        except (xml.parsers.expat.ExpatError, IndexError) as e:
            raise XmlResponseInvalidError(
                "The XML response from the OSM API is invalid: %r" % e
            )

        if single:
            return first_element
        return all_data

    def _DomGetAttributes(self, DomElement):  # noqa
        """
        Returns a formated dictionnary of attributes of a DomElement.
        """
        result = {}
        for k, v in DomElement.attributes.items():
            if k == "uid":
                v = int(v)
            elif k == "changeset":
                v = int(v)
            elif k == "version":
                v = int(v)
            elif k == "id":
                v = int(v)
            elif k == "lat":
                v = float(v)
            elif k == "lon":
                v = float(v)
            elif k == "open":
                v = (v == "true")
            elif k == "visible":
                v = (v == "true")
            elif k == "ref":
                v = int(v)
            elif k == "comments_count":
                v = int(v)
            elif k == "timestamp":
                v = self._ParseDate(v)
            elif k == "created_at":
                v = self._ParseDate(v)
            elif k == "closed_at":
                v = self._ParseDate(v)
            elif k == "date":
                v = self._ParseDate(v)
            result[k] = v
        return result

    def _DomGetTag(self, DomElement):
        """
        Returns the dictionnary of tags of a DomElement.
        """
        result = {}
        for t in DomElement.getElementsByTagName("tag"):
            k = t.attributes["k"].value
            v = t.attributes["v"].value
            result[k] = v
        return result

    def _DomGetNd(self, DomElement):
        """
        Returns the list of nodes of a DomElement.
        """
        result = []
        for t in DomElement.getElementsByTagName("nd"):
            result.append(int(int(t.attributes["ref"].value)))
        return result

    def _DomGetDiscussion(self, DomElement):
        """
        Returns the dictionnary of comments of a DomElement.
        """
        result = []
        try:
            discussion = DomElement.getElementsByTagName("discussion")[0]
            for t in discussion.getElementsByTagName("comment"):
                comment = self._DomGetAttributes(t)
                comment['text'] = self._GetXmlValue(t, "text")
                result.append(comment)
        except IndexError:
            pass
        return result

    def _DomGetComments(self, DomElement):
        """
        Returns the list of comments of a DomElement.
        """
        result = []
        for t in DomElement.getElementsByTagName("comment"):
            comment = {}
            comment['date'] = self._ParseDate(self._GetXmlValue(t, "date"))
            comment['action'] = self._GetXmlValue(t, "action")
            comment['text'] = self._GetXmlValue(t, "text")
            comment['html'] = self._GetXmlValue(t, "html")
            comment['uid'] = self._GetXmlValue(t, "uid")
            comment['user'] = self._GetXmlValue(t, "user")
            result.append(comment)
        return result

    def _DomGetMember(self, DomElement):
        """
        Returns a list of relation members.
        """
        result = []
        for m in DomElement.getElementsByTagName("member"):
            result.append(self._DomGetAttributes(m))
        return result

    def _DomParseNode(self, DomElement):
        """
        Returns NodeData for the node.
        """
        result = self._DomGetAttributes(DomElement)
        result["tag"] = self._DomGetTag(DomElement)
        return result

    def _DomParseWay(self, DomElement):
        """
        Returns WayData for the way.
        """
        result = self._DomGetAttributes(DomElement)
        result["tag"] = self._DomGetTag(DomElement)
        result["nd"] = self._DomGetNd(DomElement)
        return result

    def _DomParseRelation(self, DomElement):
        """
        Returns RelationData for the relation.
        """
        result = self._DomGetAttributes(DomElement)
        result["tag"] = self._DomGetTag(DomElement)
        result["member"] = self._DomGetMember(DomElement)
        return result

    def _DomParseChangeset(self, DomElement):
        """
        Returns ChangesetData for the changeset.
        """
        result = self._DomGetAttributes(DomElement)
        result["tag"] = self._DomGetTag(DomElement)
        result["discussion"] = self._DomGetDiscussion(DomElement)

        return result

    def _DomParseNote(self, DomElement):
        """
        Returns NoteData for the note.
        """
        result = self._DomGetAttributes(DomElement)
        result["id"] = self._GetXmlValue(DomElement, "id")
        result["status"] = self._GetXmlValue(DomElement, "status")

        result["date_created"] = self._ParseDate(
            self._GetXmlValue(DomElement, "date_created")
        )
        result["date_closed"] = self._ParseDate(
            self._GetXmlValue(DomElement, "date_closed")
        )
        result["comments"] = self._DomGetComments(DomElement)

        return result

    def _ParseDate(self, DateString):
        result = DateString
        try:
            result = datetime.strptime(DateString, "%Y-%m-%d %H:%M:%S UTC")
        except:
            try:
                result = datetime.strptime(DateString, "%Y-%m-%dT%H:%M:%SZ")
            except:
                pass

        return result

    ##################################################
    # Internal xml builder                           #
    ##################################################

    def _XmlBuild(self, ElementType, ElementData, WithHeaders=True):  # noqa

        xml = ""
        if WithHeaders:
            xml += "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            xml += "<osm version=\"0.6\" generator=\""
            xml += self._created_by + "\">\n"

        # <element attr="val">
        xml += "  <" + ElementType
        if "id" in ElementData:
            xml += " id=\"" + str(ElementData["id"]) + "\""
        if "lat" in ElementData:
            xml += " lat=\"" + str(ElementData["lat"]) + "\""
        if "lon" in ElementData:
            xml += " lon=\"" + str(ElementData["lon"]) + "\""
        if "version" in ElementData:
            xml += " version=\"" + str(ElementData["version"]) + "\""
        visible_str = str(ElementData.get("visible", True)).lower()
        xml += " visible=\"" + visible_str + "\""
        if ElementType in ["node", "way", "relation"]:
            xml += " changeset=\"" + str(self._CurrentChangesetId) + "\""
        xml += ">\n"

        # <tag... />
        for k, v in ElementData.get("tag", {}).items():
            xml += "    <tag k=\"" + self._XmlEncode(k)
            xml += "\" v=\"" + self._XmlEncode(v) + "\"/>\n"

        # <member... />
        for member in ElementData.get("member", []):
            xml += "    <member type=\"" + member["type"]
            xml += "\" ref=\"" + str(member["ref"])
            xml += "\" role=\"" + self._XmlEncode(member["role"])
            xml += "\"/>\n"

        # <nd... />
        for ref in ElementData.get("nd", []):
            xml += "    <nd ref=\"" + str(ref) + "\"/>\n"

        # </element>
        xml += "  </" + ElementType + ">\n"

        if WithHeaders:
            xml += "</osm>\n"

        return xml.encode("utf8")

    def _XmlEncode(self, text):
        return (
            text
            .replace("&", "&amp;")
            .replace("\"", "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _GetXmlValue(self, DomElement, tag):
        try:
            elem = DomElement.getElementsByTagName(tag)[0]
            return elem.firstChild.nodeValue
        except:
            return None
