from typing import Literal, TypedDict, List, Dict, Any, Protocol

# from typing import Literal, List, Optional, TypedDict, Dict

id_type = int
OsmType = Literal["node", "way", "relation"]


class MaxDict(TypedDict):
    maximum: int


class MinDict(TypedDict):
    minimum: int


class MinMaxDict(MaxDict, MinDict):
    pass


class ChangesetsDict(TypedDict):
    maximum_elements: int


class StatusDict(TypedDict):
    api: Literal["online", "readonly", "offline"]
    database: Literal["online", "readonly", "offline"]
    gpx: Literal["online", "readonly", "offline"]


class TimeoutDict(TypedDict):
    seconds: int


class TracepointsDict(TypedDict):
    per_page: int


class CapabilitiesDict(TypedDict):
    area: MaxDict
    changesets: ChangesetsDict
    status: StatusDict
    timeout: TimeoutDict
    tracepoints: TracepointsDict
    version: MinMaxDict
    waynodes: MaxDict


class RelationMemberDict(TypedDict):
    ref: id_type
    role: str  # TODO: how many roles are there?
    type: OsmType


class RealtionData(TypedDict):
    id: id_type
    member: List[RelationMemberDict]
    tag: Dict
    changeset: id_type
    version: int
    user: str
    uid: id_type
    visible: bool


OsmData = RealtionData


class ChangesetDataDict(TypedDict):
    action: Literal["delete", "", ""]
    type: OsmType
    data: OsmData


class ChangesetTagsDict(TypedDict):
    str: str


class HttpResponse:
    status_code: int
    content: str
    reason: str


class SessionLike(Protocol):
    auth: Any
    headers: dict

    def request(method: str, path: str, data: dict) -> HttpResponse: ...
