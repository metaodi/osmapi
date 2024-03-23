from typing import Literal, TypedDict

# from typing import List, Optional, Dict


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
