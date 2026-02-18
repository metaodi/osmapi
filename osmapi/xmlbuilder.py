from typing import Any, Optional, TYPE_CHECKING
from xml.dom.minidom import Element

if TYPE_CHECKING:
    from .OsmApi import OsmApi


def _xml_build(  # noqa: C901
    element_type: str,
    element_data: dict[str, Any],
    with_headers: bool = True,
    *,
    data: "OsmApi",
) -> bytes:
    xml = ""
    if with_headers:
        xml += '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<osm version="0.6" generator="'
        xml += data._created_by + '">'
        xml += "\n"

    # <element attr="val">
    xml += "  <" + element_type
    if "id" in element_data:
        xml += ' id="' + str(element_data["id"]) + '"'
    if "lat" in element_data:
        xml += ' lat="' + str(element_data["lat"]) + '"'
    if "lon" in element_data:
        xml += ' lon="' + str(element_data["lon"]) + '"'
    if "version" in element_data:
        xml += ' version="' + str(element_data["version"]) + '"'
    visible_str = str(element_data.get("visible", True)).lower()
    xml += ' visible="' + visible_str + '"'
    if element_type in ["node", "way", "relation"]:
        xml += ' changeset="' + str(data._current_changeset_id) + '"'
    xml += ">\n"

    # <tag... />
    for k, v in element_data.get("tag", {}).items():
        xml += '    <tag k="' + _xml_encode(k)
        xml += '" v="' + _xml_encode(v) + '"/>\n'

    # <member... />
    for member in element_data.get("member", []):
        xml += '    <member type="' + member["type"]
        xml += '" ref="' + str(member["ref"])
        xml += '" role="' + _xml_encode(member["role"])
        xml += '"/>\n'

    # <nd... />
    for ref in element_data.get("nd", []):
        xml += '    <nd ref="' + str(ref) + '"/>\n'

    # </element>
    xml += "  </" + element_type + ">\n"

    if with_headers:
        xml += "</osm>\n"

    return xml.encode("utf8")


def _xml_encode(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _get_xml_value(dom_element: Element, tag: str) -> Optional[str]:
    try:
        elem = dom_element.getElementsByTagName(tag)[0]
        return elem.firstChild.nodeValue  # type: ignore[union-attr]
    except Exception:
        return None
