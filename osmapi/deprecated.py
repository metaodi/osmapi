"""
Deprecated wrapper methods for backward compatibility.

These methods provide CamelCase versions of the new snake_case API.
All methods issue a DeprecationWarning and call the new snake_case methods.
"""

# This file contains all the deprecated CamelCase method wrappers
# that call the new snake_case methods with a DeprecationWarning.

DEPRECATED_METHODS = '''
    ##################################################
    # Node - Deprecated CamelCase methods           #
    ##################################################

    def NodeGet(self, NodeId: int, NodeVersion: int = -1) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`node_get` instead."""
        warnings.warn(
            "NodeGet() is deprecated, use node_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_get(NodeId, NodeVersion)

    def NodeCreate(self, NodeData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_create` instead."""
        warnings.warn(
            "NodeCreate() is deprecated, use node_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_create(NodeData)

    def NodeUpdate(self, NodeData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_update` instead."""
        warnings.warn(
            "NodeUpdate() is deprecated, use node_update() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_update(NodeData)

    def NodeDelete(self, NodeData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_delete` instead."""
        warnings.warn(
            "NodeDelete() is deprecated, use node_delete() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_delete(NodeData)

    def NodeHistory(self, NodeId: int) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_history` instead."""
        warnings.warn(
            "NodeHistory() is deprecated, use node_history() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_history(NodeId)

    def NodeWays(self, NodeId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_ways` instead."""
        warnings.warn(
            "NodeWays() is deprecated, use node_ways() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_ways(NodeId)

    def NodeRelations(self, NodeId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`node_relations` instead."""
        warnings.warn(
            "NodeRelations() is deprecated, use node_relations() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_relations(NodeId)

    def NodesGet(self, NodeIdList: list[int]) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`nodes_get` instead."""
        warnings.warn(
            "NodesGet() is deprecated, use nodes_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.nodes_get(NodeIdList)

    ##################################################
    # Way - Deprecated CamelCase methods            #
    ##################################################

    def WayGet(self, WayId: int, WayVersion: int = -1) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`way_get` instead."""
        warnings.warn(
            "WayGet() is deprecated, use way_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_get(WayId, WayVersion)

    def WayCreate(self, WayData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_create` instead."""
        warnings.warn(
            "WayCreate() is deprecated, use way_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_create(WayData)

    def WayUpdate(self, WayData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_update` instead."""
        warnings.warn(
            "WayUpdate() is deprecated, use way_update() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_update(WayData)

    def WayDelete(self, WayData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_delete` instead."""
        warnings.warn(
            "WayDelete() is deprecated, use way_delete() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_delete(WayData)

    def WayHistory(self, WayId: int) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_history` instead."""
        warnings.warn(
            "WayHistory() is deprecated, use way_history() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_history(WayId)

    def WayRelations(self, WayId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_relations` instead."""
        warnings.warn(
            "WayRelations() is deprecated, use way_relations() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_relations(WayId)

    def WayFull(self, WayId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`way_full` instead."""
        warnings.warn(
            "WayFull() is deprecated, use way_full() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.way_full(WayId)

    def WaysGet(self, WayIdList: list[int]) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`ways_get` instead."""
        warnings.warn(
            "WaysGet() is deprecated, use ways_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.ways_get(WayIdList)

    ##################################################
    # Relation - Deprecated CamelCase methods       #
    ##################################################

    def RelationGet(self, RelationId: int, RelationVersion: int = -1) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`relation_get` instead."""
        warnings.warn(
            "RelationGet() is deprecated, use relation_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_get(RelationId, RelationVersion)

    def RelationCreate(self, RelationData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_create` instead."""
        warnings.warn(
            "RelationCreate() is deprecated, use relation_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_create(RelationData)

    def RelationUpdate(self, RelationData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_update` instead."""
        warnings.warn(
            "RelationUpdate() is deprecated, use relation_update() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_update(RelationData)

    def RelationDelete(self, RelationData: dict[str, Any]) -> Optional[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_delete` instead."""
        warnings.warn(
            "RelationDelete() is deprecated, use relation_delete() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_delete(RelationData)

    def RelationHistory(self, RelationId: int) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_history` instead."""
        warnings.warn(
            "RelationHistory() is deprecated, use relation_history() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_history(RelationId)

    def RelationRelations(self, RelationId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_relations` instead."""
        warnings.warn(
            "RelationRelations() is deprecated, use relation_relations() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_relations(RelationId)

    def RelationFullRecur(self, RelationId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_full_recur` instead."""
        warnings.warn(
            "RelationFullRecur() is deprecated, use relation_full_recur() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_full_recur(RelationId)

    def RelationFull(self, RelationId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`relation_full` instead."""
        warnings.warn(
            "RelationFull() is deprecated, use relation_full() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relation_full(RelationId)

    def RelationsGet(self, RelationIdList: list[int]) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`relations_get` instead."""
        warnings.warn(
            "RelationsGet() is deprecated, use relations_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.relations_get(RelationIdList)

    ##################################################
    # Changeset - Deprecated CamelCase methods      #
    ##################################################

    @contextmanager
    def Changeset(
        self, ChangesetTags: Optional[dict[str, str]] = None
    ) -> Generator[int, None, None]:
        """.. deprecated:: Use :meth:`changeset` instead."""
        warnings.warn(
            "Changeset() is deprecated, use changeset() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        with self.changeset(ChangesetTags) as changeset_id:
            yield changeset_id

    def ChangesetGet(
        self, ChangesetId: int, include_discussion: bool = False
    ) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`changeset_get` instead."""
        warnings.warn(
            "ChangesetGet() is deprecated, use changeset_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_get(ChangesetId, include_discussion)

    def ChangesetUpdate(self, ChangesetTags: Optional[dict[str, str]] = None) -> int:
        """.. deprecated:: Use :meth:`changeset_update` instead."""
        warnings.warn(
            "ChangesetUpdate() is deprecated, use changeset_update() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_update(ChangesetTags)

    def ChangesetCreate(self, ChangesetTags: Optional[dict[str, str]] = None) -> int:
        """.. deprecated:: Use :meth:`changeset_create` instead."""
        warnings.warn(
            "ChangesetCreate() is deprecated, use changeset_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_create(ChangesetTags)

    def ChangesetClose(self) -> int:
        """.. deprecated:: Use :meth:`changeset_close` instead."""
        warnings.warn(
            "ChangesetClose() is deprecated, use changeset_close() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_close()

    def ChangesetUpload(
        self, ChangesData: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`changeset_upload` instead."""
        warnings.warn(
            "ChangesetUpload() is deprecated, use changeset_upload() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_upload(ChangesData)

    def ChangesetDownload(self, ChangesetId: int) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`changeset_download` instead."""
        warnings.warn(
            "ChangesetDownload() is deprecated, use changeset_download() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_download(ChangesetId)

    def ChangesetsGet(  # noqa
        self,
        min_lon: Optional[float] = None,
        min_lat: Optional[float] = None,
        max_lon: Optional[float] = None,
        max_lat: Optional[float] = None,
        userid: Optional[int] = None,
        username: Optional[str] = None,
        closed_after: Optional[str] = None,
        created_before: Optional[str] = None,
        only_open: bool = False,
        only_closed: bool = False,
    ) -> dict[int, dict[str, Any]]:
        """.. deprecated:: Use :meth:`changesets_get` instead."""
        warnings.warn(
            "ChangesetsGet() is deprecated, use changesets_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changesets_get(
            min_lon, min_lat, max_lon, max_lat, userid, username,
            closed_after, created_before, only_open, only_closed
        )

    def ChangesetComment(self, ChangesetId: int, comment: str) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`changeset_comment` instead."""
        warnings.warn(
            "ChangesetComment() is deprecated, use changeset_comment() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_comment(ChangesetId, comment)

    def ChangesetSubscribe(self, ChangesetId: int) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`changeset_subscribe` instead."""
        warnings.warn(
            "ChangesetSubscribe() is deprecated, use changeset_subscribe() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_subscribe(ChangesetId)

    def ChangesetUnsubscribe(self, ChangesetId: int) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`changeset_unsubscribe` instead."""
        warnings.warn(
            "ChangesetUnsubscribe() is deprecated, use changeset_unsubscribe() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.changeset_unsubscribe(ChangesetId)

    ##################################################
    # Note - Deprecated CamelCase methods           #
    ##################################################

    def NotesGet(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        limit: int = 100,
        closed: int = 7,
    ) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`notes_get` instead."""
        warnings.warn(
            "NotesGet() is deprecated, use notes_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.notes_get(min_lon, min_lat, max_lon, max_lat, limit, closed)

    def NoteGet(self, id: int) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_get` instead."""
        warnings.warn(
            "NoteGet() is deprecated, use note_get() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_get(id)

    def NoteCreate(self, NoteData: dict[str, Any]) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_create` instead."""
        warnings.warn(
            "NoteCreate() is deprecated, use note_create() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_create(NoteData)

    def NoteComment(self, NoteId: int, comment: str) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_comment` instead."""
        warnings.warn(
            "NoteComment() is deprecated, use note_comment() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_comment(NoteId, comment)

    def NoteClose(self, NoteId: int, comment: Optional[str] = None) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_close` instead."""
        warnings.warn(
            "NoteClose() is deprecated, use note_close() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_close(NoteId, comment)

    def NoteReopen(self, NoteId: int, comment: Optional[str] = None) -> dict[str, Any]:
        """.. deprecated:: Use :meth:`note_reopen` instead."""
        warnings.warn(
            "NoteReopen() is deprecated, use note_reopen() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.note_reopen(NoteId, comment)

    def NotesSearch(
        self, query: str, limit: int = 100, closed: int = 7
    ) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`notes_search` instead."""
        warnings.warn(
            "NotesSearch() is deprecated, use notes_search() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.notes_search(query, limit, closed)

    def _NoteAction(
        self, path: str, comment: Optional[str] = None, optionalAuth: bool = True
    ) -> dict[str, Any]:
        """Internal method - calls _note_action."""
        return self._note_action(path, comment, optionalAuth)

    ##################################################
    # Map - Deprecated CamelCase methods            #
    ##################################################

    def Map(
        self, min_lon: float, min_lat: float, max_lon: float, max_lat: float
    ) -> list[dict[str, Any]]:
        """.. deprecated:: Use :meth:`map` instead."""
        warnings.warn(
            "Map() is deprecated, use map() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.map(min_lon, min_lat, max_lon, max_lat)
'''
