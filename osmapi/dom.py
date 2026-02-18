"""
DOM parsing for the OpenStreetMap API.
"""

from datetime import datetime
import xml.dom.minidom
import xml.parsers.expat
import logging
from typing import Any, Union, Optional
from xml.dom.minidom import Element

from . import errors
from . import xmlbuilder

logger = logging.getLogger(__name__)


def OsmResponseToDom(
    response: bytes, tag: str, single: bool = False, allow_empty: bool = False
) -> Union[Element, list[Element]]:
    """
    Returns the (sub-) DOM parsed from an OSM response
    """
    try:
        dom = xml.dom.minidom.parseString(response)
        osm_dom = dom.getElementsByTagName("osm")[0]
        all_data = osm_dom.getElementsByTagName(tag)
        first_element = all_data[0]
    except IndexError as e:
        if allow_empty:
            return []
        raise errors.XmlResponseInvalidError(
            f"The XML response from the OSM API is invalid: {e!r}"
        )
    except xml.parsers.expat.ExpatError as e:
        raise errors.XmlResponseInvalidError(
            f"The XML response from the OSM API is invalid: {e!r}"
        )

    if single:
        return first_element
    return list(all_data)


def DomParseNode(dom_element: Element) -> dict[str, Any]:
    """
    Returns NodeData for the node.
    """
    result = _DomGetAttributes(dom_element)
    result["tag"] = _DomGetTag(dom_element)
    return result


def DomParseWay(dom_element: Element) -> dict[str, Any]:
    """
    Returns WayData for the way.
    """
    result = _DomGetAttributes(dom_element)
    result["tag"] = _DomGetTag(dom_element)
    result["nd"] = _DomGetNd(dom_element)
    return result


def DomParseRelation(dom_element: Element) -> dict[str, Any]:
    """
    Returns RelationData for the relation.
    """
    result = _DomGetAttributes(dom_element)
    result["tag"] = _DomGetTag(dom_element)
    result["member"] = _DomGetMember(dom_element)
    return result


def DomParseChangeset(
    dom_element: Element, include_discussion: bool = False
) -> dict[str, Any]:
    """
    Returns ChangesetData for the changeset.
    """
    result = _DomGetAttributes(dom_element)
    result["tag"] = _DomGetTag(dom_element)
    if include_discussion:
        result["discussion"] = _DomGetDiscussion(dom_element)

    return result


def DomParseNote(dom_element: Element) -> dict[str, Any]:
    """
    Returns NoteData for the note.
    """
    result = _DomGetAttributes(dom_element)
    result["id"] = xmlbuilder._get_xml_value(dom_element, "id")
    result["status"] = xmlbuilder._get_xml_value(dom_element, "status")

    result["date_created"] = _ParseDate(
        xmlbuilder._get_xml_value(dom_element, "date_created")
    )
    result["date_closed"] = _ParseDate(
        xmlbuilder._get_xml_value(dom_element, "date_closed")
    )
    result["comments"] = _DomGetComments(dom_element)

    return result


def _DomGetAttributes(dom_element: Element) -> dict[str, Any]:
    """
    Returns a formated dictionnary of attributes of a dom_element.
    """

    def is_true(v: str) -> bool:
        return v == "true"

    attribute_mapping: dict[str, Any] = {
        "uid": int,
        "changeset": int,
        "version": int,
        "id": int,
        "lat": float,
        "lon": float,
        "open": is_true,
        "visible": is_true,
        "ref": int,
        "comments_count": int,
        "timestamp": _ParseDate,
        "created_at": _ParseDate,
        "closed_at": _ParseDate,
        "date": _ParseDate,
    }
    result: dict[str, Any] = {}
    for k, v in dom_element.attributes.items():
        try:
            result[k] = attribute_mapping[k](v)
        except KeyError:
            result[k] = v
    return result


def _DomGetTag(dom_element: Element) -> dict[str, str]:
    """
    Returns the dictionnary of tags of a dom_element.
    """
    result: dict[str, str] = {}
    for t in dom_element.getElementsByTagName("tag"):
        k = t.attributes["k"].value
        v = t.attributes["v"].value
        result[k] = v
    return result


def _DomGetNd(dom_element: Element) -> list[int]:
    """
    Returns the list of nodes of a dom_element.
    """
    result: list[int] = []
    for t in dom_element.getElementsByTagName("nd"):
        result.append(int(int(t.attributes["ref"].value)))
    return result


def _DomGetDiscussion(dom_element: Element) -> list[dict[str, Any]]:
    """
    Returns the dictionnary of comments of a dom_element.
    """
    result: list[dict[str, Any]] = []
    try:
        discussion = dom_element.getElementsByTagName("discussion")[0]
        for t in discussion.getElementsByTagName("comment"):
            comment = _DomGetAttributes(t)
            comment["text"] = xmlbuilder._get_xml_value(t, "text")
            result.append(comment)
    except IndexError:
        pass
    return result


def _DomGetComments(dom_element: Element) -> list[dict[str, Any]]:
    """
    Returns the list of comments of a dom_element.
    """
    result: list[dict[str, Any]] = []
    for t in dom_element.getElementsByTagName("comment"):
        comment: dict[str, Any] = {}
        comment["date"] = _ParseDate(xmlbuilder._get_xml_value(t, "date"))
        comment["action"] = xmlbuilder._get_xml_value(t, "action")
        comment["text"] = xmlbuilder._get_xml_value(t, "text")
        comment["html"] = xmlbuilder._get_xml_value(t, "html")
        comment["uid"] = xmlbuilder._get_xml_value(t, "uid")
        comment["user"] = xmlbuilder._get_xml_value(t, "user")
        result.append(comment)
    return result


def _DomGetMember(dom_element: Element) -> list[dict[str, Any]]:
    """
    Returns a list of relation members.
    """
    result: list[dict[str, Any]] = []
    for m in dom_element.getElementsByTagName("member"):
        result.append(_DomGetAttributes(m))
    return result


def _ParseDate(DateString: Optional[str]) -> Union[datetime, str, None]:
    date_formats = ["%Y-%m-%d %H:%M:%S UTC", "%Y-%m-%dT%H:%M:%SZ"]
    for date_format in date_formats:
        try:
            result = datetime.strptime(DateString, date_format)  # type: ignore[arg-type]  # noqa: E501
            return result
        except (ValueError, TypeError):
            logger.debug(f"{DateString} does not match {date_format}")

    return DateString
