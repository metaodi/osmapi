"""
XML generation for requests to the OpenStreetMap API.

The documents are assembled as `xml.etree.ElementTree` elements and
serialized by `ElementTree.tostring`, so escaping is the standard library's
job. Building them by hand used to miss everything but `& " < >`, which
silently corrupted any tag value containing a newline or a tab: XML
normalizes those to a space in an attribute value unless they are written as
character references (see issue #216).
"""

import xml.etree.ElementTree as ET
from typing import Any, TYPE_CHECKING
from xml.etree.ElementTree import Element

if TYPE_CHECKING:
    from .OsmApi import OsmApi

_XML_PROLOG = '<?xml version="1.0" encoding="UTF-8"?>\n'


def _xml_build(
    element_type: str,
    element_data: dict[str, Any],
    with_headers: bool = True,
    *,
    data: "OsmApi",
) -> bytes:
    """
    Returns the XML document for a write of `element_data`.

    With `with_headers` the element is wrapped in an `<osm>` envelope and
    prefixed with the XML prolog, otherwise only the element itself is
    returned — that is how `OsmApi._add_changeset_data` collects the parts of
    an `<osmChange>` upload.
    """
    root = _xml_element(element_type, element_data, data=data)
    prolog = ""
    if with_headers:
        osm = ET.Element("osm", {"version": "0.6", "generator": data._created_by})
        osm.append(root)
        root = osm
        prolog = _XML_PROLOG

    ET.indent(root, space="  ")
    return f"{prolog}{ET.tostring(root, encoding='unicode')}\n".encode("utf-8")


def _xml_element(
    element_type: str, element_data: dict[str, Any], *, data: "OsmApi"
) -> ET.Element:
    """
    Returns `element_data` as an element of type `element_type`.
    """
    attributes: dict[str, str] = {
        key: str(element_data[key])
        for key in ("id", "lat", "lon", "version")
        if key in element_data
    }
    attributes["visible"] = str(element_data.get("visible", True)).lower()
    if element_type in ("node", "way", "relation"):
        attributes["changeset"] = str(data._current_changeset_id)

    element = ET.Element(element_type, attributes)
    for k, v in element_data.get("tag", {}).items():
        ET.SubElement(element, "tag", {"k": k, "v": v})
    for member in element_data.get("member", []):
        ET.SubElement(
            element,
            "member",
            {
                "type": member["type"],
                "ref": str(member["ref"]),
                "role": member["role"],
            },
        )
    for ref in element_data.get("nd", []):
        ET.SubElement(element, "nd", {"ref": str(ref)})
    return element


def _get_xml_value(dom_element: Element, tag: str) -> str | None:
    elem = dom_element.find(tag)
    if elem is None:
        return None
    return elem.text
