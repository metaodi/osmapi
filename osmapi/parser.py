import xml.dom.minidom
import xml.parsers.expat
from typing import List, Dict, Any

from . import errors
from . import dom


def ParseOsm(data: bytes) -> List[Dict[str, Any]]:
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
        data_parsed = xml.dom.minidom.parseString(data)
        data_parsed = data_parsed.getElementsByTagName("osm")[0]
    except (xml.parsers.expat.ExpatError, IndexError) as e:
        raise errors.XmlResponseInvalidError(
            f"The XML response from the OSM API is invalid: {e!r}"
        ) from e

    result: List[Dict[str, Any]] = []
    for elem in data_parsed.childNodes:
        if elem.nodeName == "node":
            result.append({"type": elem.nodeName, "data": dom.DomParseNode(elem)})
        elif elem.nodeName == "way":
            result.append({"type": elem.nodeName, "data": dom.DomParseWay(elem)})
        elif elem.nodeName == "relation":
            result.append({"type": elem.nodeName, "data": dom.DomParseRelation(elem)})
    return result


def ParseOsc(data: bytes) -> List[Dict[str, Any]]:
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
        data_parsed = xml.dom.minidom.parseString(data)
        data_parsed = data_parsed.getElementsByTagName("osmChange")[0]
    except (xml.parsers.expat.ExpatError, IndexError) as e:
        raise errors.XmlResponseInvalidError(
            f"The XML response from the OSM API is invalid: {e!r}"
        ) from e

    result: List[Dict[str, Any]] = []
    for action in data_parsed.childNodes:
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


def ParseNotes(data: bytes) -> List[Dict[str, Any]]:
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
    result: List[Dict[str, Any]] = []
    for noteElement in noteElements:
        note = dom.DomParseNote(noteElement)
        result.append(note)
    return result
