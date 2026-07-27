"""
Way operations for the OpenStreetMap API.

This module provides pythonic (snake_case) methods for working with OSM ways.
"""

from collections.abc import Iterator
from typing import Any, TYPE_CHECKING

from . import dom, parser

if TYPE_CHECKING:
    from .OsmApi import OsmApi


class WayMixin:
    """Mixin providing way-related operations with pythonic method names."""

    def way_get(self: "OsmApi", way_id: int, way_version: int = -1) -> dict[str, Any]:
        """
        Returns way with `way_id` as a dict:

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

        If `way_version` is supplied, this specific version is returned,
        otherwise the latest version is returned.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/way/{way_id}"
        if way_version != -1:
            uri += f"/{way_version}"
        data = self._session._get(uri)
        way = dom.OsmResponseToDom(data, tag="way", single=True)
        return dom.dom_parse_way(way)

    def way_create(self: "OsmApi", way_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Creates a way based on the supplied `way_data` dict:

            #!python
            {
                'nd': [] list of nodes,
                'tag': {} dict of tags,
            }

        Returns updated `way_data` (without timestamp):

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

        If no session is provided to authenticate the request,
        `OsmApi.AuthenticationMissingError` is raised.

        If the supplied information contain an existing node,
        `OsmApi.OsmTypeAlreadyExistsError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("create", "way", way_data)

    def way_update(self: "OsmApi", way_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Updates way with the supplied `way_data` dict:

            #!python
            {
                'id': id of way,
                'nd': [] list of nodes,
                'tag': {},
                'version': version number of way,
            }

        Returns updated `way_data` (without timestamp):

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

        If no session is provided to authenticate the request,
        `OsmApi.AuthenticationMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If there is already an open changeset,
        `OsmApi.ChangesetAlreadyOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("modify", "way", way_data)

    def way_delete(self: "OsmApi", way_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Delete way with `way_data`:

            #!python
            {
                'id': id of way,
                'nd': [] list of nodes,
                'tag': dict of tags,
                'version': version number of way,
            }

        Returns updated `way_data` (without timestamp):

            #!python
            {
                'id': id of way,
                'nd': [] list of nodes,
                'tag': dict of tags,
                'changeset': id of changeset of last change,
                'version': version number of way,
                'user': username of last change,
                'uid': id of user of last change,
                'visible': True|False
            }

        If no session is provided to authenticate the request,
        `OsmApi.AuthenticationMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("delete", "way", way_data)

    def way_history(self: "OsmApi", way_id: int) -> dict[int, dict[str, Any]]:
        """
        Returns dict with version as key:

            #!python
            {
                1: dict of way version 1,
                2: dict of way version 2,
                ...
            }

        The whole history is held in memory at once; use `way_history_iter`
        to work through the versions one by one instead.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        return {way["version"]: way for way in self.way_history_iter(way_id)}

    def way_history_iter(self: "OsmApi", way_id: int) -> Iterator[dict[str, Any]]:
        """
        Yields every version of the way with `way_id`, oldest first.

        Same data as `way_history`, but the response is parsed while it is
        being read and only one version is held in memory at a time. The
        version number of each dict is available as its `version` key.

        The connection stays open until the iterator is exhausted, so consume
        it (or close it) promptly.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/way/{way_id}/history"
        with self._session._get_stream(uri) as data:
            for way in dom.OsmResponseToDom(data, tag="way"):
                yield dom.dom_parse_way(way)

    def way_relations(self: "OsmApi", way_id: int) -> list[dict[str, Any]]:
        """
        Returns a list of dicts of relation data containing way `way_id`:

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

        The `way_id` is a unique identifier for a way.
        """
        uri = f"/api/0.6/way/{way_id}/relations"
        data = self._session._get(uri)
        relations = dom.OsmResponseToDom(data, tag="relation", allow_empty=True)
        result: list[dict[str, Any]] = []
        for relation in relations:
            relation_data = dom.dom_parse_relation(relation)
            result.append(relation_data)
        return result

    def way_full(self: "OsmApi", way_id: int) -> list[dict[str, Any]]:
        """
        Returns the full data for way `way_id` as list of dicts:

            #!python
            [
                {
                    'type': node|way|relation,
                    'data': {} data dict for node|way|relation
                },
                { ... }
            ]

        The `way_id` is a unique identifier for a way.

        The whole response is held in memory at once; use `way_full_iter` to
        work through the elements one by one instead.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        return list(self.way_full_iter(way_id))

    def way_full_iter(self: "OsmApi", way_id: int) -> Iterator[dict[str, Any]]:
        """
        Yields the full data for way `way_id`, one element at a time.

        Same data as `way_full`, but the response is parsed while it is being
        read and only one element is held in memory at a time.

        The connection stays open until the iterator is exhausted, so consume
        it (or close it) promptly.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/way/{way_id}/full"
        with self._session._get_stream(uri) as data:
            yield from parser.iter_osm(data)

    def ways_get(self: "OsmApi", way_id_list: list[int]) -> dict[int, dict[str, Any]]:
        """
        Returns dict with the id of the way as a key for
        each way in `way_id_list`:

            #!python
            {
                '1234': dict of way data,
                '5678': dict of way data,
                ...
            }

        `way_id_list` is a list containing unique identifiers for multiple ways.
        """
        way_list = ",".join([str(x) for x in way_id_list])
        uri = f"/api/0.6/ways?ways={way_list}"
        data = self._session._get(uri)
        ways = dom.OsmResponseToDom(data, tag="way")
        result: dict[int, dict[str, Any]] = {}
        for way in ways:
            way_data = dom.dom_parse_way(way)
            result[way_data["id"]] = way_data
        return result
