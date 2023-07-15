def _XmlBuild(ElementType, ElementData, WithHeaders=True, data=None):  # noqa
    xml = ""
    if WithHeaders:
        xml += '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<osm version="0.6" generator="'
        xml += data._created_by + '">\n'

    # <element attr="val">
    xml += "  <" + ElementType
    if "id" in ElementData:
        xml += ' id="' + str(ElementData["id"]) + '"'
    if "lat" in ElementData:
        xml += ' lat="' + str(ElementData["lat"]) + '"'
    if "lon" in ElementData:
        xml += ' lon="' + str(ElementData["lon"]) + '"'
    if "version" in ElementData:
        xml += ' version="' + str(ElementData["version"]) + '"'
    visible_str = str(ElementData.get("visible", True)).lower()
    xml += ' visible="' + visible_str + '"'
    if ElementType in ["node", "way", "relation"]:
        xml += ' changeset="' + str(data._CurrentChangesetId) + '"'
    xml += ">\n"

    # <tag... />
    for k, v in ElementData.get("tag", {}).items():
        xml += '    <tag k="' + _XmlEncode(k)
        xml += '" v="' + _XmlEncode(v) + '"/>\n'

    # <member... />
    for member in ElementData.get("member", []):
        xml += '    <member type="' + member["type"]
        xml += '" ref="' + str(member["ref"])
        xml += '" role="' + _XmlEncode(member["role"])
        xml += '"/>\n'

    # <nd... />
    for ref in ElementData.get("nd", []):
        xml += '    <nd ref="' + str(ref) + '"/>\n'

    # </element>
    xml += "  </" + ElementType + ">\n"

    if WithHeaders:
        xml += "</osm>\n"

    return xml.encode("utf8")


def _XmlEncode(text):
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _GetXmlValue(DomElement, tag):
    try:
        elem = DomElement.getElementsByTagName(tag)[0]
        return elem.firstChild.nodeValue
    except Exception:
        return None
