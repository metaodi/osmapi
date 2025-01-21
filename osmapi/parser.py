import xml.dom.minidom
import xml.parsers.expat

from . import errors
from . import dom


def ParseOsm(data):
    """
    Parse osm data.

    Returns list of dict:

        #!python
        {
            type: node|way|relation,
            data: {}
        }
    """
    try:
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osm")[0]
    except (xml.parsers.expat.ExpatError, IndexError) as e:
        raise errors.XmlResponseInvalidError(
            f"The XML response from the OSM API is invalid: {e!r}"
        ) from e

    result = []
    for elem in data.childNodes:
        if elem.nodeName == "node":
            result.append({"type": elem.nodeName, "data": dom.DomParseNode(elem)})
        elif elem.nodeName == "way":
            result.append({"type": elem.nodeName, "data": dom.DomParseWay(elem)})
        elif elem.nodeName == "relation":
            result.append({"type": elem.nodeName, "data": dom.DomParseRelation(elem)})
    return result


def ParseOsc(data):
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
    try:
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osmChange")[0]
    except (xml.parsers.expat.ExpatError, IndexError) as e:
        raise errors.XmlResponseInvalidError(
            f"The XML response from the OSM API is invalid: {e!r}"
        ) from e

    result = []
    for action in data.childNodes:
        if action.nodeName == "#text":
            continue
        for elem in action.childNodes:
            if elem.nodeName == "node":
                result.append(
                    {
                        "action": action.nodeName,
                        "type": elem.nodeName,
                        "data": dom.DomParseNode(elem),
                    }
                )
            elif elem.nodeName == "way":
                result.append(
                    {
                        "action": action.nodeName,
                        "type": elem.nodeName,
                        "data": dom.DomParseWay(elem),
                    }
                )
            elif elem.nodeName == "relation":
                result.append(
                    {
                        "action": action.nodeName,
                        "type": elem.nodeName,
                        "data": dom.DomParseRelation(elem),
                    }
                )
    return result


def ParseNotes(data):
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
    noteElements = dom.OsmResponseToDom(data, tag="note", allow_empty=True)
    result = []
    for noteElement in noteElements:
        note = dom.DomParseNote(noteElement)
        result.append(note)
    return result
