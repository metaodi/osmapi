"""
XML parsing for the OpenStreetMap API.

Responses are parsed incrementally with `xml.etree.ElementTree.iterparse`:
every element is handed to a `dom_parse_*` function and dropped again right
away, so a response never exists as a complete tree in memory. The previous
`xml.dom.minidom` implementation needed roughly 40 times the size of the
document for that tree, which made large responses (the history of a big
relation, a `map` call) unreasonably expensive.
"""

import io
import logging
import sys
import xml.etree.ElementTree as ET
from collections.abc import Container, Generator, Iterator
from datetime import datetime
from typing import IO, Any, Literal, overload
from xml.etree.ElementTree import Element

from . import errors
from . import xmlbuilder

logger = logging.getLogger(__name__)

XmlSource = bytes | IO[bytes]
"""A complete response body, or a stream to read it from as it arrives."""


def _iter_elements(
    source: XmlSource, tags: Container[str], root_tag: str | None = None
) -> Generator[tuple[str | None, Element], None, None]:
    """
    Yields a `(parent tag, element)` pair for every element with a tag in `tags`.

    The document is parsed as it is read and each element is discarded again
    as soon as the consumer asks for the next one, so the memory needed does
    not grow with the size of the response. The flip side is that a yielded
    element must be consumed before iteration continues: afterwards it is
    emptied and detached from its parent.

    If `root_tag` is given, the document is required to have that root
    element, otherwise `OsmApi.XmlResponseInvalidError` is raised. The same
    error is raised for a malformed document, but only once iteration reaches
    the point where the parser gives up.
    """
    stream = io.BytesIO(source) if isinstance(source, bytes) else source
    stack: list[Element] = []
    try:
        for event, element in ET.iterparse(stream, events=("start", "end")):
            if event == "start":
                if not stack and root_tag is not None and element.tag != root_tag:
                    raise errors.XmlResponseInvalidError(
                        "The XML response from the OSM API is invalid: expected a "
                        f"<{root_tag}> element, got <{element.tag}>"
                    )
                stack.append(element)
                continue

            stack.pop()
            if element.tag not in tags:
                continue
            parent = stack[-1] if stack else None
            yield (parent.tag if parent is not None else None), element

            # Release the element again: clear() drops its content, removing
            # it from its parent drops the element itself. Without this the
            # tree would still grow to the size of the whole document.
            element.clear()
            if parent is not None:
                parent.remove(element)
    except ET.ParseError as e:
        raise errors.XmlResponseInvalidError(
            f"The XML response from the OSM API is invalid: {e!r}"
        ) from e


@overload
def OsmResponseToDom(
    response: XmlSource, tag: str, *, single: Literal[True], allow_empty: bool = False
) -> Element: ...


@overload
def OsmResponseToDom(
    response: XmlSource,
    tag: str,
    single: Literal[False] = False,
    allow_empty: bool = False,
) -> Iterator[Element]: ...


def OsmResponseToDom(
    response: XmlSource, tag: str, single: bool = False, allow_empty: bool = False
) -> Element | Iterator[Element]:
    """
    Returns the elements with the given `tag` of an OSM response.

    With `single`, only the first matching element is returned and the rest of
    the response is not parsed at all. Otherwise an iterator over all matching
    elements is returned, which parses the response lazily — see
    `_iter_elements` for what that means for the elements it yields.

    If the response contains no matching element and `allow_empty` is not set,
    `OsmApi.XmlResponseInvalidError` is raised.
    """
    elements = _iter_elements(response, (tag,), root_tag="osm")
    if single:
        try:
            return next(elements)[1]
        except StopIteration:
            raise errors.XmlResponseInvalidError(
                "The XML response from the OSM API is invalid: "
                f"it contains no <{tag}> element"
            ) from None
        finally:
            # Closing before the element is consumed is what keeps it intact.
            elements.close()
    return _require_elements(elements, tag, allow_empty)


def _require_elements(
    elements: Iterator[tuple[str | None, Element]], tag: str, allow_empty: bool
) -> Iterator[Element]:
    """
    Drops the parent tags of `_iter_elements` and rejects an empty result.
    """
    found = False
    for _, element in elements:
        found = True
        yield element
    if not found and not allow_empty:
        raise errors.XmlResponseInvalidError(
            "The XML response from the OSM API is invalid: "
            f"it contains no <{tag}> element"
        )


def dom_parse_node(dom_element: Element) -> dict[str, Any]:
    """
    Returns NodeData for the node.
    """
    result = _dom_get_attributes(dom_element)
    result["tag"] = _dom_get_tag(dom_element)
    return result


def dom_parse_way(dom_element: Element) -> dict[str, Any]:
    """
    Returns WayData for the way.
    """
    result = _dom_get_attributes(dom_element)
    result["tag"] = _dom_get_tag(dom_element)
    result["nd"] = _dom_get_nd(dom_element)
    return result


def dom_parse_relation(dom_element: Element) -> dict[str, Any]:
    """
    Returns RelationData for the relation.
    """
    result = _dom_get_attributes(dom_element)
    result["tag"] = _dom_get_tag(dom_element)
    result["member"] = _dom_get_member(dom_element)
    return result


def dom_parse_changeset(
    dom_element: Element, include_discussion: bool = False
) -> dict[str, Any]:
    """
    Returns ChangesetData for the changeset.
    """
    result = _dom_get_attributes(dom_element)
    result["tag"] = _dom_get_tag(dom_element)
    if include_discussion:
        result["discussion"] = _dom_get_discussion(dom_element)

    return result


def dom_parse_note(dom_element: Element) -> dict[str, Any]:
    """
    Returns NoteData for the note.
    """
    result = _dom_get_attributes(dom_element)
    result["id"] = xmlbuilder._get_xml_value(dom_element, "id")
    result["status"] = xmlbuilder._get_xml_value(dom_element, "status")

    result["date_created"] = _parse_date(
        xmlbuilder._get_xml_value(dom_element, "date_created")
    )
    result["date_closed"] = _parse_date(
        xmlbuilder._get_xml_value(dom_element, "date_closed")
    )
    result["comments"] = _dom_get_comments(dom_element)

    return result


def _dedupe(value: str) -> str:
    """
    Returns a shared instance of `value`.

    An OSM response repeats the same strings over and over: attribute names,
    tag keys, member roles and types, user names. Keeping one instance of each
    instead of one per occurrence roughly halves the memory the parsed result
    occupies.
    """
    return sys.intern(value)


def _dom_get_attributes(dom_element: Element) -> dict[str, Any]:
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
        "timestamp": _parse_date,
        "created_at": _parse_date,
        "closed_at": _parse_date,
        "date": _parse_date,
    }
    result: dict[str, Any] = {}
    for k, v in dom_element.attrib.items():
        try:
            result[_dedupe(k)] = attribute_mapping[k](v)
        except KeyError:
            result[_dedupe(k)] = _dedupe(v)
    return result


def _dom_get_tag(dom_element: Element) -> dict[str, str]:
    """
    Returns the dictionnary of tags of a dom_element.
    """
    return {
        _dedupe(t.attrib["k"]): _dedupe(t.attrib["v"])
        for t in dom_element.iterfind("tag")
    }


def _dom_get_nd(dom_element: Element) -> list[int]:
    """
    Returns the list of nodes of a dom_element.
    """
    return [int(t.attrib["ref"]) for t in dom_element.iterfind("nd")]


def _dom_get_discussion(dom_element: Element) -> list[dict[str, Any]]:
    """
    Returns the dictionnary of comments of a dom_element.
    """
    result: list[dict[str, Any]] = []
    discussion = dom_element.find("discussion")
    if discussion is None:
        return result
    for t in discussion.iterfind("comment"):
        comment = _dom_get_attributes(t)
        comment["text"] = xmlbuilder._get_xml_value(t, "text")
        result.append(comment)
    return result


def _dom_get_comments(dom_element: Element) -> list[dict[str, Any]]:
    """
    Returns the list of comments of a dom_element.
    """
    result: list[dict[str, Any]] = []
    for t in dom_element.iterfind("comments/comment"):
        comment: dict[str, Any] = {}
        comment["date"] = _parse_date(xmlbuilder._get_xml_value(t, "date"))
        comment["action"] = xmlbuilder._get_xml_value(t, "action")
        comment["text"] = xmlbuilder._get_xml_value(t, "text")
        comment["html"] = xmlbuilder._get_xml_value(t, "html")
        comment["uid"] = xmlbuilder._get_xml_value(t, "uid")
        comment["user"] = xmlbuilder._get_xml_value(t, "user")
        result.append(comment)
    return result


def _dom_get_member(dom_element: Element) -> list[dict[str, Any]]:
    """
    Returns a list of relation members.
    """
    return [_dom_get_attributes(m) for m in dom_element.iterfind("member")]


def _parse_date(date_string: str | None) -> datetime | str | None:
    date_formats = ["%Y-%m-%d %H:%M:%S UTC", "%Y-%m-%dT%H:%M:%SZ"]
    for date_format in date_formats:
        try:
            result = datetime.strptime(date_string, date_format)  # type: ignore[arg-type]  # noqa: E501
            return result
        except (ValueError, TypeError):
            logger.debug(f"{date_string} does not match {date_format}")

    return date_string
