from datetime import datetime
import xml.dom.minidom
import xml.parsers.expat
import logging

from . import errors
from . import xmlbuilder


logger = logging.getLogger(__name__)


def OsmResponseToDom(response, tag, single=False, allow_empty=False):
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
    return all_data


def DomParseNode(DomElement):
    """
    Returns NodeData for the node.
    """
    result = _DomGetAttributes(DomElement)
    result["tag"] = _DomGetTag(DomElement)
    return result


def DomParseWay(DomElement):
    """
    Returns WayData for the way.
    """
    result = _DomGetAttributes(DomElement)
    result["tag"] = _DomGetTag(DomElement)
    result["nd"] = _DomGetNd(DomElement)
    return result


def DomParseRelation(DomElement):
    """
    Returns RelationData for the relation.
    """
    result = _DomGetAttributes(DomElement)
    result["tag"] = _DomGetTag(DomElement)
    result["member"] = _DomGetMember(DomElement)
    return result


def DomParseChangeset(DomElement, include_discussion=False):
    """
    Returns ChangesetData for the changeset.
    """
    result = _DomGetAttributes(DomElement)
    result["tag"] = _DomGetTag(DomElement)
    if include_discussion:
        result["discussion"] = _DomGetDiscussion(DomElement)

    return result


def DomParseNote(DomElement):
    """
    Returns NoteData for the note.
    """
    result = _DomGetAttributes(DomElement)
    result["id"] = xmlbuilder._GetXmlValue(DomElement, "id")
    result["status"] = xmlbuilder._GetXmlValue(DomElement, "status")

    result["date_created"] = _ParseDate(
        xmlbuilder._GetXmlValue(DomElement, "date_created")
    )
    result["date_closed"] = _ParseDate(
        xmlbuilder._GetXmlValue(DomElement, "date_closed")
    )
    result["comments"] = _DomGetComments(DomElement)

    return result


def _DomGetAttributes(DomElement):
    """
    Returns a formated dictionnary of attributes of a DomElement.
    """

    def is_true(v):
        return v == "true"

    attribute_mapping = {
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
    result = {}
    for k, v in DomElement.attributes.items():
        try:
            result[k] = attribute_mapping[k](v)
        except KeyError:
            result[k] = v
    return result


def _DomGetTag(DomElement):
    """
    Returns the dictionnary of tags of a DomElement.
    """
    result = {}
    for t in DomElement.getElementsByTagName("tag"):
        k = t.attributes["k"].value
        v = t.attributes["v"].value
        result[k] = v
    return result


def _DomGetNd(DomElement):
    """
    Returns the list of nodes of a DomElement.
    """
    result = []
    for t in DomElement.getElementsByTagName("nd"):
        result.append(int(int(t.attributes["ref"].value)))
    return result


def _DomGetDiscussion(DomElement):
    """
    Returns the dictionnary of comments of a DomElement.
    """
    result = []
    try:
        discussion = DomElement.getElementsByTagName("discussion")[0]
        for t in discussion.getElementsByTagName("comment"):
            comment = _DomGetAttributes(t)
            comment["text"] = xmlbuilder._GetXmlValue(t, "text")
            result.append(comment)
    except IndexError:
        pass
    return result


def _DomGetComments(DomElement):
    """
    Returns the list of comments of a DomElement.
    """
    result = []
    for t in DomElement.getElementsByTagName("comment"):
        comment = {}
        comment["date"] = _ParseDate(xmlbuilder._GetXmlValue(t, "date"))
        comment["action"] = xmlbuilder._GetXmlValue(t, "action")
        comment["text"] = xmlbuilder._GetXmlValue(t, "text")
        comment["html"] = xmlbuilder._GetXmlValue(t, "html")
        comment["uid"] = xmlbuilder._GetXmlValue(t, "uid")
        comment["user"] = xmlbuilder._GetXmlValue(t, "user")
        result.append(comment)
    return result


def _DomGetMember(DomElement):
    """
    Returns a list of relation members.
    """
    result = []
    for m in DomElement.getElementsByTagName("member"):
        result.append(_DomGetAttributes(m))
    return result


def _ParseDate(DateString):
    date_formats = ["%Y-%m-%d %H:%M:%S UTC", "%Y-%m-%dT%H:%M:%SZ"]
    for date_format in date_formats:
        try:
            result = datetime.strptime(DateString, date_format)
            return result
        except (ValueError, TypeError):
            logger.debug(f"{DateString} does not match {date_format}")

    return DateString
