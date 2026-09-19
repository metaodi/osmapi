"""
Parsers for whole OSM documents.

Each parser comes in two flavours: a function returning a list, and an
`iter_*` variant returning an iterator. The iterator parses the document as it
is read and never holds more than one element at a time, which is what makes
it possible to work through a response that does not fit in memory (see
`dom` for the details).
"""

from collections.abc import Callable, Iterator
from typing import Any
from xml.etree.ElementTree import Element

from . import dom

_OSM_ELEMENTS: dict[str, Callable[[Element], dict[str, Any]]] = {
    "node": dom.dom_parse_node,
    "way": dom.dom_parse_way,
    "relation": dom.dom_parse_relation,
}


def parse_osm(data: dom.XmlSource) -> list[dict[str, Any]]:
    """
    Parse osm data.

    Returns list of dict:

        #!python
        {
            type: node|way|relation,
            data: {}
        }
    """
    return list(iter_osm(data))


def iter_osm(data: dom.XmlSource) -> Iterator[dict[str, Any]]:
    """
    Parse osm data, yielding one element at a time.

    Yields the same dicts as `parse_osm`, but without building the list of all
    of them.
    """
    for _, element in dom._iter_elements(data, _OSM_ELEMENTS, root_tag="osm"):
        yield {"type": element.tag, "data": _OSM_ELEMENTS[element.tag](element)}


def parse_osc(data: dom.XmlSource) -> list[dict[str, Any]]:
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
    return list(iter_osc(data))


def iter_osc(data: dom.XmlSource) -> Iterator[dict[str, Any]]:
    """
    Parse osc data, yielding one change at a time.

    Yields the same dicts as `parse_osc`, but without building the list of all
    of them.
    """
    for action, element in dom._iter_elements(
        data, _OSM_ELEMENTS, root_tag="osmChange"
    ):
        yield {
            "action": action,
            "type": element.tag,
            "data": _OSM_ELEMENTS[element.tag](element),
        }


def parse_notes(data: dom.XmlSource) -> list[dict[str, Any]]:
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
    return list(iter_notes(data))


def iter_notes(data: dom.XmlSource) -> Iterator[dict[str, Any]]:
    """
    Parse notes data, yielding one note at a time.

    Yields the same dicts as `parse_notes`, but without building the list of
    all of them.
    """
    for element in dom.OsmResponseToDom(data, tag="note", allow_empty=True):
        yield dom.dom_parse_note(element)
