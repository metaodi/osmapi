"""
Node operations for the OpenStreetMap API.
"""

from typing import Any, Optional, TYPE_CHECKING, cast
from xml.dom.minidom import Element

from . import dom

if TYPE_CHECKING:
    from .OsmApi import OsmApi


class NodeMixin:
    """Mixin providing node-related operations with pythonic method names."""

    def node_get(
        self: "OsmApi", node_id: int, node_version: int = -1
    ) -> dict[str, Any]:
        """
        Returns node with `node_id` as a dict:

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

        If `node_version` is supplied, this specific version is returned,
        otherwise the latest version is returned.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/node/{node_id}"
        if node_version != -1:
            uri += f"/{node_version}"
        data = self._session._get(uri)
        node_element = cast(
            Element, dom.OsmResponseToDom(data, tag="node", single=True)
        )
        return dom.dom_parse_node(node_element)

    def node_create(
        self: "OsmApi", node_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        Creates a node based on the supplied `node_data` dict:

            #!python
            {
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': {},
            }

        Returns updated `node_data` (without timestamp):

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
        return self._do("create", "node", node_data)

    def node_update(
        self: "OsmApi", node_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        Updates node with the supplied `node_data` dict:

            #!python
            {
                'id': id of node,
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': {},
                'version': version number of node,
            }

        Returns updated `node_data` (without timestamp):

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
        return self._do("modify", "node", node_data)

    def node_delete(
        self: "OsmApi", node_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        Delete node with `node_data`:

            #!python
            {
                'id': id of node,
                'lat': latitude of node,
                'lon': longitude of node,
                'tag': dict of tags,
                'version': version number of node,
            }

        Returns updated `node_data` (without timestamp):

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

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("delete", "node", node_data)

    def node_history(self: "OsmApi", node_id: int) -> dict[int, dict[str, Any]]:
        """
        Returns dict with version as key:

            #!python
            {
                1: dict of node version 1,
                2: dict of node version 2,
                ...
            }

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/node/{node_id}/history"
        data = self._session._get(uri)
        node_list = cast(list[Element], dom.OsmResponseToDom(data, tag="node"))
        result = {}
        for node in node_list:
            node_data = dom.dom_parse_node(node)
            result[node_data["version"]] = node_data
        return result

    def node_ways(self: "OsmApi", node_id: int) -> list[dict[str, Any]]:
        """
        Returns list of dicts of ways that use the node with `node_id`:

            #!python
            [
                {
                    'id': id of way,
                    'nd': list of node ids,
                    'tag': dict of tags,
                    'changeset': id of changeset of last change,
                    'version': version number of way,
                    'user': username of user that made the last change,
                    'uid': id of user that made the last change,
                    'timestamp': timestamp of last change,
                    'visible': True|False
                },
                ...
            ]

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/node/{node_id}/ways"
        data = self._session._get(uri)
        way_list = cast(
            list[Element], dom.OsmResponseToDom(data, tag="way", allow_empty=True)
        )
        return [dom.dom_parse_way(way) for way in way_list]

    def node_relations(self: "OsmApi", node_id: int) -> list[dict[str, Any]]:
        """
        Returns list of dicts of relations that use the node with `node_id`:

            #!python
            [
                {
                    'id': id of relation,
                    'member': [
                        {
                            'ref': reference id,
                            'role': role,
                            'type': node|way|relation
                        },
                        ...
                    ],
                    'tag': dict of tags,
                    'changeset': id of changeset of last change,
                    'version': version number of relation,
                    'user': username of user that made the last change,
                    'uid': id of user that made the last change,
                    'timestamp': timestamp of last change,
                    'visible': True|False
                },
                ...
            ]

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/node/{node_id}/relations"
        data = self._session._get(uri)
        relation_list = cast(
            list[Element], dom.OsmResponseToDom(data, tag="relation", allow_empty=True)
        )
        return [dom.dom_parse_relation(rel) for rel in relation_list]

    def nodes_get(self: "OsmApi", node_id_list: list[int]) -> dict[int, dict[str, Any]]:
        """
        Returns dict with id as key:

            #!python
            {
                node_id: dict of node,
                ...
            }

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        nodes = ",".join([str(x) for x in node_id_list])
        uri = f"/api/0.6/nodes?nodes={nodes}"
        data = self._session._get(uri)
        node_list = cast(list[Element], dom.OsmResponseToDom(data, tag="node"))
        result = {}
        for node in node_list:
            node_data = dom.dom_parse_node(node)
            result[node_data["id"]] = node_data
        return result
