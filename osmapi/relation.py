"""
Relation operations for the OpenStreetMap API.

This module provides pythonic (snake_case) methods for working with OSM relations.
"""

from typing import Any, TYPE_CHECKING, cast
from xml.dom.minidom import Element

from . import dom, parser

if TYPE_CHECKING:
    from .OsmApi import OsmApi


class RelationMixin:
    """Mixin providing relation-related operations with pythonic method names."""

    def relation_get(
        self: "OsmApi", relation_id: int, relation_version: int = -1
    ) -> dict[str, Any]:
        """
        Returns relation with `relation_id` as a dict.

        If `relation_version` is supplied, this specific version is returned,
        otherwise the latest version is returned.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/relation/{relation_id}"
        if relation_version != -1:
            uri += f"/{relation_version}"
        data = self._session._get(uri)
        relation = cast(
            Element, dom.OsmResponseToDom(data, tag="relation", single=True)
        )
        return dom.dom_parse_relation(relation)

    def relation_create(
        self: "OsmApi", relation_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Creates a relation based on the supplied `relation_data` dict.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If the supplied information contain an existing relation,
        `OsmApi.OsmTypeAlreadyExistsError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("create", "relation", relation_data)

    def relation_update(
        self: "OsmApi", relation_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Updates relation with the supplied `relation_data` dict.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("modify", "relation", relation_data)

    def relation_delete(
        self: "OsmApi", relation_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Delete relation with `relation_data`.

        If no authentication information are provided,
        `OsmApi.UsernamePasswordMissingError` is raised.

        If there is no open changeset,
        `OsmApi.NoChangesetOpenError` is raised.

        If the changeset is already closed,
        `OsmApi.ChangesetClosedApiError` is raised.
        """
        return self._do("delete", "relation", relation_data)

    def relation_history(self: "OsmApi", relation_id: int) -> dict[int, dict[str, Any]]:
        """
        Returns dict with version as key.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/relation/{relation_id}/history"
        data = self._session._get(uri)
        relations = cast(list[Element], dom.OsmResponseToDom(data, tag="relation"))
        result: dict[int, dict[str, Any]] = {}
        for relation in relations:
            relation_data = dom.dom_parse_relation(relation)
            result[relation_data["version"]] = relation_data
        return result

    def relation_relations(self: "OsmApi", relation_id: int) -> list[dict[str, Any]]:
        """
        Returns a list of dicts of relation data containing relation `relation_id`.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/relation/{relation_id}/relations"
        data = self._session._get(uri)
        relations = cast(
            list[Element], dom.OsmResponseToDom(data, tag="relation", allow_empty=True)
        )
        result: list[dict[str, Any]] = []
        for relation in relations:
            relation_data = dom.dom_parse_relation(relation)
            result.append(relation_data)
        return result

    def relation_full_recur(self: "OsmApi", relation_id: int) -> list[dict[str, Any]]:
        """
        Returns the full data (all levels) for relation `relation_id` as list of dicts.

        This function is useful for relations containing other relations.

        If you don't need all levels, use `relation_full` instead,
        which return only 2 levels.

        If any relation (on any level) has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        data = []
        todo = [relation_id]
        done = []
        while todo:
            rid = todo.pop(0)
            done.append(rid)
            temp = self.relation_full(rid)
            for item in temp:
                if item["type"] != "relation":
                    continue
                if item["data"]["id"] in done:
                    continue
                todo.append(item["data"]["id"])
            data += temp
        return data

    def relation_full(self: "OsmApi", relation_id: int) -> list[dict[str, Any]]:
        """
        Returns the full data (two levels) for relation `relation_id` as list of dicts.

        If you need all levels, use `relation_full_recur`.

        If the requested element has been deleted,
        `OsmApi.ElementDeletedApiError` is raised.

        If the requested element can not be found,
        `OsmApi.ElementNotFoundApiError` is raised.
        """
        uri = f"/api/0.6/relation/{relation_id}/full"
        data = self._session._get(uri)
        return parser.parse_osm(data)

    def relations_get(
        self: "OsmApi", relation_id_list: list[int]
    ) -> dict[int, dict[str, Any]]:
        """
        Returns dict with the id of the relation as a key
        for each relation in `relation_id_list`.

        `relation_id_list` is a list containing unique identifiers
        for multiple relations.
        """
        relation_list = ",".join([str(x) for x in relation_id_list])
        uri = f"/api/0.6/relations?relations={relation_list}"
        data = self._session._get(uri)
        relations = cast(list[Element], dom.OsmResponseToDom(data, tag="relation"))
        result: dict[int, dict[str, Any]] = {}
        for relation in relations:
            relation_data = dom.dom_parse_relation(relation)
            result[relation_data["id"]] = relation_data
        return result
