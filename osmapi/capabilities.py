"""
Capabilities and miscellaneous operations for the OpenStreetMap API.
"""

from typing import Any, TYPE_CHECKING, cast
from xml.dom.minidom import Element

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

        api_element = cast(Element, dom.OsmResponseToDom(data, tag="api", single=True))
        result: dict[str, Any] = {}
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

    def map(
        self: "OsmApi", min_lon: float, min_lat: float, max_lon: float, max_lat: float
    ) -> list[dict[str, Any]]:
        """
        Download data in bounding box.

        Returns list of dict with type and data.
        """
        uri = f"/api/0.6/map?bbox={min_lon:f},{min_lat:f},{max_lon:f},{max_lat:f}"
        data = self._session._get(uri)
        return parser.parse_osm(data)
