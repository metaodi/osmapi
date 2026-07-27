"""
Capabilities and miscellaneous operations for the OpenStreetMap API.
"""

from collections.abc import Iterator
from typing import Any, TYPE_CHECKING

from . import dom, parser

if TYPE_CHECKING:
    from .OsmApi import OsmApi


class CapabilitiesMixin:
    """Mixin providing capabilities and misc operations with pythonic method names."""

    def capabilities(self: "OsmApi") -> dict[str, dict[str, Any]]:
        """
        Returns the API capabilities as a dict.

        The capabilities can be used by a client to
        gain insights of the server in use.
        """
        uri = "/api/capabilities"
        data = self._session._get(uri)

        api_element = dom.OsmResponseToDom(data, tag="api", single=True)
        result: dict[str, Any] = {}
        for elem in api_element:
            result[elem.tag] = {}
            for k, v in elem.attrib.items():
                try:
                    result[elem.tag][k] = float(v)
                except ValueError:
                    result[elem.tag][k] = v
        return result

    def map(
        self: "OsmApi", min_lon: float, min_lat: float, max_lon: float, max_lat: float
    ) -> list[dict[str, Any]]:
        """
        Download data in bounding box.

        Returns list of dict with type and data.

        The whole bounding box is held in memory at once; use `map_iter` to
        work through the elements one by one instead.
        """
        return list(self.map_iter(min_lon, min_lat, max_lon, max_lat))

    def map_iter(
        self: "OsmApi", min_lon: float, min_lat: float, max_lon: float, max_lat: float
    ) -> Iterator[dict[str, Any]]:
        """
        Download data in bounding box, yielding one element at a time.

        Same data as `map`, but the response is parsed while it is being read
        and only one element is held in memory at a time.

        The connection stays open until the iterator is exhausted, so consume
        it (or close it) promptly.
        """
        uri = f"/api/0.6/map?bbox={min_lon:f},{min_lat:f},{max_lon:f},{max_lat:f}"
        with self._session._get_stream(uri) as data:
            yield from parser.iter_osm(data)
