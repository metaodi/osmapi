# -*- coding: utf-8 -*-

from __future__ import (absolute_import, print_function, unicode_literals)
try:
    import httplib
except ImportError:
    import http.client as httplib
import base64
import xml.dom.minidom
import time
import sys
import urllib

# Python 3.x
if getattr(urllib, 'urlencode', None) is None:
    urllib.urlencode = urllib.parse.urlencode

from . import __version__


class ApiError(Exception):

    def __init__(self, status, reason, payload):
        self.status = status
        self.reason = reason
        self.payload = payload

    def __str__(self):
        return (
            "Request failed: %s - %s - %s"
            % (str(self.status), self.reason, self.payload)
        )


class OsmApi:
    def __init__(
            self,
            username=None,
            password=None,
            passwordfile=None,
            appid="",
            created_by="osmapi/"+__version__,
            api="www.openstreetmap.org",
            changesetauto=False,
            changesetautotags={},
            changesetautosize=500,
            changesetautomulti=1,
            debug=False):

        # debug
        self._debug = debug

        # Get username
        if username:
            self._username = username
        elif passwordfile:
            pass_line = open(passwordfile).readline()
            self._username = pass_line.split(":")[0].strip()

        # Get password
        if password:
            self._password = password
        elif passwordfile:
            for l in open(passwordfile).readlines():
                l = l.strip().split(":")
                if l[0] == self._username:
                    self._password = l[1]

        # Changest informations
        # auto create and close changesets
        self._changesetauto = changesetauto
        # tags for automatic created changesets
        self._changesetautotags = changesetautotags
        # change count for auto changeset
        self._changesetautosize = changesetautosize
        # change count for auto changeset
        self._changesetautosize = changesetautosize
        # close a changeset every # upload
        self._changesetautomulti = changesetautomulti
        self._changesetautocpt = 0
        # data to upload for auto group
        self._changesetautodata = []

        # Get API
        self._api = api

        # Get created_by
        if not appid:
            self._created_by = created_by
        else:
            self._created_by = appid + " (" + created_by + ")"

        # Initialisation
        self._CurrentChangesetId = 0

        # Http connection
        self._conn = httplib.HTTPConnection(self._api, 80)

    def __del__(self):
        if self._changesetauto:
            self._changesetautoflush(True)
        return None

    ##################################################
    # Capabilities                                   #
    ##################################################

    def Capabilities(self):
        """
        Returns ApiCapabilities.
        """
        uri = "/api/capabilities"
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osm")[0]
        data = data.getElementsByTagName("api")[0]
        result = {}
        for elem in data.childNodes:
            if elem.nodeType != elem.ELEMENT_NODE:
                continue
            result[elem.nodeName] = {}
            for k, v in elem.attributes.items():
                try:
                    result[elem.nodeName][k] = float(v)
                except:
                    result[elem.nodeName][k] = v
        return result

    ##################################################
    # Node                                           #
    ##################################################

    def NodeGet(self, NodeId, NodeVersion=-1):
        """
        Returns NodeData for node #NodeId.
        """
        uri = "/api/0.6/node/"+str(NodeId)
        if NodeVersion != -1:
            uri += "/"+str(NodeVersion)
        data = self._get(uri)
        if not data:
            return data
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osm")[0]
        data = data.getElementsByTagName("node")[0]
        return self._DomParseNode(data)

    def NodeCreate(self, NodeData):
        """
        Creates a node.
        Returns updated NodeData (without timestamp).
        """
        return self._do("create", "node", NodeData)

    def NodeUpdate(self, NodeData):
        """
        Updates node with NodeData.
        Returns updated NodeData (without timestamp).
        """
        return self._do("modify", "node", NodeData)

    def NodeDelete(self, NodeData):
        """
        Delete node with NodeData.
        Returns updated NodeData (without timestamp).
        """
        return self._do("delete", "node", NodeData)

    def NodeHistory(self, NodeId):
        """
        Returns dict(NodeVerrsion: NodeData).
        """
        uri = "/api/0.6/node/"+str(NodeId)+"/history"
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = {}
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("node"):
            data = self._DomParseNode(data)
            result[data["version"]] = data
        return result

    def NodeWays(self, NodeId):
        """
        Returns [WayData, ... ] containing node #NodeId.
        """
        uri = "/api/0.6/node/%d/ways" % NodeId
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = []
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("way"):
            data = self._DomParseRelation(data)
            result.append(data)
        return result

    def NodeRelations(self, NodeId):
        """
        Returns [RelationData, ... ] containing node #NodeId.
        """
        uri = "/api/0.6/node/%d/relations" % NodeId
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = []
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("relation"):
            data = self._DomParseRelation(data)
            result.append(data)
        return result

    def NodesGet(self, NodeIdList):
        """
        Returns dict(NodeId: NodeData) for each node in NodeIdList
        """
        uri = "/api/0.6/nodes?nodes=" + ",".join([str(x) for x in NodeIdList])
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = {}
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("node"):
            data = self._DomParseNode(data)
            result[data["id"]] = data
        return result

    ##################################################
    # Way                                            #
    ##################################################

    def WayGet(self, WayId, WayVersion=-1):
        """
        Returns WayData for way #WayId.
        """
        uri = "/api/0.6/way/"+str(WayId)
        if WayVersion != -1:
            uri += "/"+str(WayVersion)
        data = self._get(uri)
        if not data:
            return data
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osm")[0]
        data = data.getElementsByTagName("way")[0]
        return self._DomParseWay(data)

    def WayCreate(self, WayData):
        """
        Creates a way.
        Returns updated WayData (without timestamp).
        """
        return self._do("create", "way", WayData)

    def WayUpdate(self, WayData):
        """
        Updates way with WayData.
        Returns updated WayData (without timestamp).
        """
        return self._do("modify", "way", WayData)

    def WayDelete(self, WayData):
        """
        Delete way with WayData.
        Returns updated WayData (without timestamp).
        """
        return self._do("delete", "way", WayData)

    def WayHistory(self, WayId):
        """
        Returns dict(WayVerrsion: WayData).
        """
        uri = "/api/0.6/way/"+str(WayId)+"/history"
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = {}
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("way"):
            data = self._DomParseWay(data)
            result[data["version"]] = data
        return result

    def WayRelations(self, WayId):
        """
        Returns [RelationData, ...] containing way #WayId.
        """
        uri = "/api/0.6/way/%d/relations" % WayId
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = []
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("relation"):
            data = self._DomParseRelation(data)
            result.append(data)
        return result

    def WayFull(self, WayId):
        """
        Return full data for way WayId as list
        of {type: node|way|relation, data: {}}.
        """
        uri = "/api/0.6/way/"+str(WayId)+"/full"
        data = self._get(uri)
        return self.ParseOsm(data)

    def WaysGet(self, WayIdList):
        """
        Returns dict(WayId: WayData) for each way in WayIdList
        """
        uri = "/api/0.6/ways?ways=" + ",".join([str(x) for x in WayIdList])
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = {}
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("way"):
            data = self._DomParseWay(data)
            result[data["id"]] = data
        return result

    ##################################################
    # Relation                                       #
    ##################################################

    def RelationGet(self, RelationId, RelationVersion=-1):
        """
        Returns RelationData for relation #RelationId.
        """
        uri = "/api/0.6/relation/"+str(RelationId)
        if RelationVersion != -1:
            uri += "/"+str(RelationVersion)
        data = self._get(uri)
        if not data:
            return data
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osm")[0]
        data = data.getElementsByTagName("relation")[0]
        return self._DomParseRelation(data)

    def RelationCreate(self, RelationData):
        """
        Creates a relation.
        Returns updated RelationData (without timestamp).
        """
        return self._do("create", "relation", RelationData)

    def RelationUpdate(self, RelationData):
        """
        Updates relation with RelationData.
        Returns updated RelationData (without timestamp).
        """
        return self._do("modify", "relation", RelationData)

    def RelationDelete(self, RelationData):
        """
        Delete relation with RelationData.
        Returns updated RelationData (without timestamp).
        """
        return self._do("delete", "relation", RelationData)

    def RelationHistory(self, RelationId):
        """
        Returns dict(RelationVerrsion: RelationData).
        """
        uri = "/api/0.6/relation/"+str(RelationId)+"/history"
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = {}
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("relation"):
            data = self._DomParseRelation(data)
            result[data["version"]] = data
        return result

    def RelationRelations(self, RelationId):
        """
        Returns list of RelationData containing relation #RelationId.
        """
        uri = "/api/0.6/relation/%d/relations" % RelationId
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = []
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("relation"):
            data = self._DomParseRelation(data)
            result.append(data)
        return result

    def RelationFullRecur(self, RelationId):
        """
        Return full data for relation RelationId.
        Recurisve version relation of relations.
        """
        data = []
        todo = [RelationId]
        done = []
        while todo:
            rid = todo.pop(0)
            done.append(rid)
            temp = self.RelationFull(rid)
            for item in temp:
                if item["type"] != "relation":
                    continue
                if item["data"]["id"] in done:
                    continue
                todo.append(item["data"]["id"])
            data += temp
        return data

    def RelationFull(self, RelationId):
        """
        Return full data for relation RelationId as
        list of {type: node|way|relation, data: {}}.
        """
        uri = "/api/0.6/relation/"+str(RelationId)+"/full"
        data = self._get(uri)
        return self.ParseOsm(data)

    def RelationsGet(self, RelationIdList):
        """
        Returns dict(RelationId: RelationData)
        for each relation in RelationIdList
        """
        relation_list = ",".join([str(x) for x in RelationIdList])
        uri = "/api/0.6/relations?relations=" + relation_list
        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        result = {}
        osm_data = data.getElementsByTagName("osm")[0]
        for data in osm_data.getElementsByTagName("relation"):
            data = self._DomParseRelation(data)
            result[data["id"]] = data
        return result

    ##################################################
    # Changeset                                      #
    ##################################################

    def ChangesetGet(self, ChangesetId):
        """
        Returns ChangesetData for changeset #ChangesetId.
        """
        data = self._get("/api/0.6/changeset/"+str(ChangesetId))
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osm")[0]
        data = data.getElementsByTagName("changeset")[0]
        return self._DomParseChangeset(data)

    def ChangesetUpdate(self, ChangesetTags={}):
        """
        Updates current changeset with ChangesetTags.
        """
        if not self._CurrentChangesetId:
            raise Exception("No changeset currently opened")
        if "created_by" not in ChangesetTags:
            ChangesetTags["created_by"] = self._created_by
        self._put(
            "/api/0.6/changeset/" + str(self._CurrentChangesetId),
            self._XmlBuild("changeset", {"tag": ChangesetTags})
        )
        return self._CurrentChangesetId

    def ChangesetCreate(self, ChangesetTags={}):
        """
        Opens a changeset. Returns #ChangesetId.
        """
        if self._CurrentChangesetId:
            raise Exception("Changeset already opened")
        if "created_by" not in ChangesetTags:
            ChangesetTags["created_by"] = self._created_by
        result = self._put(
            "/api/0.6/changeset/create",
            self._XmlBuild("changeset", {"tag": ChangesetTags})
        )
        self._CurrentChangesetId = int(result)
        return self._CurrentChangesetId

    def ChangesetClose(self):
        """
        Closes current changeset. Returns #ChangesetId.
        """
        if not self._CurrentChangesetId:
            raise Exception("No changeset currently opened")
        self._put(
            "/api/0.6/changeset/"+str(self._CurrentChangesetId)+"/close",
            ""
        )
        CurrentChangesetId = self._CurrentChangesetId
        self._CurrentChangesetId = 0
        return CurrentChangesetId

    def ChangesetUpload(self, ChangesData):
        """
        Upload data.
        ChangesData is a list of dict
        {
            type: node|way|relation,
            action: create|delete|modify,
            data: {}
        }.
        Returns list with updated ids.
        """
        data = ""
        data += "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        data += "<osmChange version=\"0.6\" generator=\""
        data += self._created_by + "\">\n"
        for change in ChangesData:
            data += "<"+change["action"]+">\n"
            change["data"]["changeset"] = self._CurrentChangesetId
            data += self._XmlBuild(
                change["type"],
                change["data"],
                False
            ).decode("utf-8")
            data += "</"+change["action"]+">\n"
        data += "</osmChange>"
        data = self._http(
            "POST",
            "/api/0.6/changeset/"+str(self._CurrentChangesetId)+"/upload",
            True,
            data.encode("utf-8")
        )
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("diffResult")[0]
        data = [x for x in data.childNodes if x.nodeType == x.ELEMENT_NODE]
        for i in range(len(ChangesData)):
            if ChangesData[i]["action"] == "delete":
                ChangesData[i]["data"].pop("version")
            else:
                new_id = int(data[i].getAttribute("new_id"))
                ChangesData[i]["data"]["id"] = new_id
                new_version = int(data[i].getAttribute("new_version"))
                ChangesData[i]["data"]["version"] = new_version
        return ChangesData

    def ChangesetDownload(self, ChangesetId):
        """
        Download data from a changeset.
        Returns list of dict
        {
            type: node|way|relation,
            action: create|delete|modify,
            data: {}
        }.
        """
        uri = "/api/0.6/changeset/"+str(ChangesetId)+"/download"
        data = self._get(uri)
        return self.ParseOsc(data)

    def ChangesetsGet(  # noqa
            self,
            min_lon=None,
            min_lat=None,
            max_lon=None,
            max_lat=None,
            userid=None,
            username=None,
            closed_after=None,
            created_before=None,
            only_open=False,
            only_closed=False):
        """
        Returns dict(ChangsetId: ChangesetData) matching all criteria.
        """

        uri = "/api/0.6/changesets"
        params = {}
        if min_lon or min_lat or max_lon or max_lat:
            params["bbox"] = ",".join(
                [
                    str(min_lon),
                    str(min_lat),
                    str(max_lon),
                    str(max_lat)
                ]
            )
        if userid:
            params["user"] = userid
        if username:
            params["display_name"] = username
        if closed_after and not created_before:
            params["time"] = closed_after
        if created_before:
            if not closed_after:
                closed_after = "1970-01-01T00:00:00Z"
            params["time"] = closed_after + "," + created_before
        if only_open:
            params["open"] = 1
        if only_closed:
            params["closed"] = 1

        if params:
            uri += "?" + urllib.urlencode(params)

        data = self._get(uri)
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osm")[0]
        data = data.getElementsByTagName("changeset")
        result = {}
        for curChangeset in data:
            tmpCS = self._DomParseChangeset(curChangeset)
            result[tmpCS["id"]] = tmpCS
        return result

    ##################################################
    # Other                                          #
    ##################################################

    def Map(self, min_lon, min_lat, max_lon, max_lat):
        """
        Download data in bounding box.
        Returns list of dict
        {
            type: node|way|relation,
            data: {}
        }.
        """
        uri = (
            "/api/0.6/map?bbox=%f,%f,%f,%f"
            % (min_lon, min_lat, max_lon, max_lat)
        )
        data = self._get(uri)
        return self.ParseOsm(data)

    ##################################################
    # Data parser                                    #
    ##################################################

    def ParseOsm(self, data):
        """
        Parse osm data.
        Returns list of dict
        {
            type: node|way|relation,
            data: {}
        }.
        """
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osm")[0]
        result = []
        for elem in data.childNodes:
            if elem.nodeName == "node":
                result.append({
                    "type": elem.nodeName,
                    "data": self._DomParseNode(elem)
                })
            elif elem.nodeName == "way":
                result.append({
                    "type": elem.nodeName,
                    "data": self._DomParseWay(elem)
                })
            elif elem.nodeName == "relation":
                result.append({
                    "type": elem.nodeName,
                    "data": self._DomParseRelation(elem)
                })
        return result

    def ParseOsc(self, data):
        """
        Parse osc data.
        Returns list of dict
        {
            type: node|way|relation,
            action: create|delete|modify,
            data: {}
        }.
        """
        data = xml.dom.minidom.parseString(data)
        data = data.getElementsByTagName("osmChange")[0]
        result = []
        for action in data.childNodes:
            if action.nodeName == "#text":
                continue
            for elem in action.childNodes:
                if elem.nodeName == "node":
                    result.append({
                        "action": action.nodeName,
                        "type": elem.nodeName,
                        "data": self._DomParseNode(elem)
                    })
                elif elem.nodeName == "way":
                    result.append({
                        "action": action.nodeName,
                        "type": elem.nodeName,
                        "data": self._DomParseWay(elem)
                    })
                elif elem.nodeName == "relation":
                    result.append({
                        "action": action.nodeName,
                        "type": elem.nodeName,
                        "data": self._DomParseRelation(elem)
                    })
        return result

    ##################################################
    # Internal http function                         #
    ##################################################

    def _do(self, action, OsmType, OsmData):
        if self._changesetauto:
            self._changesetautodata.append({
                "action": action,
                "type": OsmType,
                "data": OsmData
            })
            self._changesetautoflush()
            return None
        else:
            return self._do_manu(action, OsmType, OsmData)

    def _do_manu(self, action, OsmType, OsmData):
        if not self._CurrentChangesetId:
            raise Exception(
                "You need to open a changeset before uploading data"
            )
        if "timestamp" in OsmData:
            OsmData.pop("timestamp")
        OsmData["changeset"] = self._CurrentChangesetId
        if action == "create":
            if OsmData.get("id", -1) > 0:
                raise Exception("This "+OsmType+" already exists")
            result = self._put(
                "/api/0.6/" + OsmType + "/create",
                self._XmlBuild(OsmType, OsmData)
            )
            OsmData["id"] = int(result.strip())
            OsmData["version"] = 1
            return OsmData
        elif action == "modify":
            result = self._put(
                "/api/0.6/" + OsmType + "/" + str(OsmData["id"]),
                self._XmlBuild(OsmType, OsmData)
            )
            OsmData["version"] = int(result.strip())
            return OsmData
        elif action == "delete":
            result = self._delete(
                "/api/0.6/" + OsmType + "/" + str(OsmData["id"]),
                self._XmlBuild(OsmType, OsmData)
            )
            OsmData["version"] = int(result.strip())
            OsmData["visible"] = False
            return OsmData

    def flush(self):
        return self._changesetautoflush(True)

    def _changesetautoflush(self, force=False):
        autosize = self._changesetautosize
        while ((len(self._changesetautodata) >= autosize) or
                (force and self._changesetautodata)):
            if self._changesetautocpt == 0:
                self.ChangesetCreate(self._changesetautotags)
            self.ChangesetUpload(
                self._changesetautodata[:autosize]
            )
            self._changesetautodata = self._changesetautodata[autosize:]
            self._changesetautocpt += 1
            if self._changesetautocpt == self._changesetautomulti:
                self.ChangesetClose()
                self._changesetautocpt = 0
        if self._changesetautocpt and force:
            self.ChangesetClose()
            self._changesetautocpt = 0
        return None

    def _http_request(self, cmd, path, auth, send):  # noqa
        if self._debug:
            path2 = path
            if len(path2) > 50:
                path2 = path2[:50]+"[...]"
            error_msg = (
                "%s %s %s"
                % (time.strftime("%Y-%m-%d %H:%M:%S"), cmd, path2)
            )
            print(error_msg, file=sys.stderr)
        self._conn.putrequest(cmd, path)
        self._conn.putheader('User-Agent', self._created_by)
        if auth:
            base64_user_pass = base64.encodestring(
                self._username + ':' + self._password
            ).strip()
            self._conn.putheader(
                'Authorization',
                'Basic ' + base64_user_pass
            )
        if send is not None:
            self._conn.putheader('Content-Length', len(send))
        self._conn.endheaders()
        if send:
            self._conn.send(send)
        response = self._conn.getresponse()
        if response.status != 200:
            payload = response.read().strip()
            if response.status == 410:
                return None
            raise ApiError(response.status, response.reason, payload)
        if self._debug:
            error_msg = (
                "%s %s %s"
                % (time.strftime("%Y-%m-%d %H:%M:%S"), cmd, path2)
            )
            print(error_msg, file=sys.stderr)
        return response.read()

    def _http(self, cmd, path, auth, send):  # noqa
        i = 0
        while True:
            i += 1
            try:
                return self._http_request(cmd, path, auth, send)
            except ApiError as e:
                if e.status >= 500:
                    if i == 5:
                        raise
                    if i != 1:
                        time.sleep(5)
                    self._conn = httplib.HTTPConnection(self._api, 80)
                else:
                    raise
            except Exception:
                if i == 5:
                    raise
                if i != 1:
                    time.sleep(5)
                self._conn = httplib.HTTPConnection(self._api, 80)

    def _get(self, path):
        return self._http('GET', path, False, None)

    def _put(self, path, data):
        return self._http('PUT', path, True, data)

    def _delete(self, path, data):
        return self._http('DELETE', path, True, data)

    ##################################################
    # Internal dom function                          #
    ##################################################

    def _DomGetAttributes(self, DomElement):  # noqa
        """
        Returns a formated dictionnary of attributes of a DomElement.
        """
        result = {}
        for k, v in DomElement.attributes.items():
            if k == "uid":
                v = int(v)
            elif k == "changeset":
                v = int(v)
            elif k == "version":
                v = int(v)
            elif k == "id":
                v = int(v)
            elif k == "lat":
                v = float(v)
            elif k == "lon":
                v = float(v)
            elif k == "open":
                v = (v == "true")
            elif k == "visible":
                v = (v == "true")
            elif k == "ref":
                v = int(v)
            result[k] = v
        return result

    def _DomGetTag(self, DomElement):
        """
        Returns the dictionnary of tags of a DomElement.
        """
        result = {}
        for t in DomElement.getElementsByTagName("tag"):
            k = t.attributes["k"].value
            v = t.attributes["v"].value
            result[k] = v
        return result

    def _DomGetNd(self, DomElement):
        """
        Returns the list of nodes of a DomElement.
        """
        result = []
        for t in DomElement.getElementsByTagName("nd"):
            result.append(int(int(t.attributes["ref"].value)))
        return result

    def _DomGetMember(self, DomElement):
        """
        Returns a list of relation members.
        """
        result = []
        for m in DomElement.getElementsByTagName("member"):
            result.append(self._DomGetAttributes(m))
        return result

    def _DomParseNode(self, DomElement):
        """
        Returns NodeData for the node.
        """
        result = self._DomGetAttributes(DomElement)
        result["tag"] = self._DomGetTag(DomElement)
        return result

    def _DomParseWay(self, DomElement):
        """
        Returns WayData for the way.
        """
        result = self._DomGetAttributes(DomElement)
        result["tag"] = self._DomGetTag(DomElement)
        result["nd"] = self._DomGetNd(DomElement)
        return result

    def _DomParseRelation(self, DomElement):
        """
        Returns RelationData for the relation.
        """
        result = self._DomGetAttributes(DomElement)
        result["tag"] = self._DomGetTag(DomElement)
        result["member"] = self._DomGetMember(DomElement)
        return result

    def _DomParseChangeset(self, DomElement):
        """
        Returns ChangesetData for the changeset.
        """
        result = self._DomGetAttributes(DomElement)
        result["tag"] = self._DomGetTag(DomElement)
        return result

    ##################################################
    # Internal xml builder                           #
    ##################################################

    def _XmlBuild(self, ElementType, ElementData, WithHeaders=True):  # noqa

        xml = ""
        if WithHeaders:
            xml += "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            xml += "<osm version=\"0.6\" generator=\""
            xml += self._created_by + "\">\n"

        # <element attr="val">
        xml += "  <" + ElementType
        if "id" in ElementData:
            xml += " id=\"" + str(ElementData["id"]) + "\""
        if "lat" in ElementData:
            xml += " lat=\"" + str(ElementData["lat"]) + "\""
        if "lon" in ElementData:
            xml += " lon=\"" + str(ElementData["lon"]) + "\""
        if "version" in ElementData:
            xml += " version=\"" + str(ElementData["version"]) + "\""
        visible_str = str(ElementData.get("visible", True)).lower()
        xml += " visible=\"" + visible_str + "\""
        if ElementType in ["node", "way", "relation"]:
            xml += " changeset=\"" + str(self._CurrentChangesetId) + "\""
        xml += ">\n"

        # <tag... />
        for k, v in ElementData.get("tag", {}).items():
            xml += "    <tag k=\"" + self._XmlEncode(k)
            xml += "\" v=\"" + self._XmlEncode(v)+"\"/>\n"

        # <member... />
        for member in ElementData.get("member", []):
            xml += "    <member type=\"" + member["type"]
            xml += "\" ref=\"" + str(member["ref"])
            xml += "\" role=\"" + self._XmlEncode(member["role"])
            xml += "\"/>\n"

        # <nd... />
        for ref in ElementData.get("nd", []):
            xml += "    <nd ref=\""+str(ref)+"\"/>\n"

        # </element>
        xml += "  </" + ElementType + ">\n"

        if WithHeaders:
            xml += "</osm>\n"

        return xml.encode("utf8")

    def _XmlEncode(self, text):
        return (
            text
            .replace("&", "&amp;")
            .replace("\"", "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
