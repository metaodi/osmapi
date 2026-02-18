from . import osmapi_test
import osmapi
from unittest import mock
import datetime


class TestOsmApiRelation(osmapi_test.TestOsmApi):
    def test_relation_get(self):
        self._session_mock()
        result = self.api.relation_get(321)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], self.api_base + "/api/0.6/relation/321")
        self.assertEqual(
            result,
            {
                "id": 321,
                "changeset": 434,
                "uid": 12,
                "timestamp": datetime.datetime(2009, 9, 15, 22, 24, 25),
                "visible": True,
                "version": 1,
                "user": "green525",
                "tag": {
                    "admin_level": "9",
                    "boundary": "administrative",
                    "type": "multipolygon",
                },
                "member": [
                    {"ref": 6908, "role": "outer", "type": "way"},
                    {"ref": 6352, "role": "outer", "type": "way"},
                    {"ref": 5669, "role": "outer", "type": "way"},
                    {"ref": 5682, "role": "outer", "type": "way"},
                    {"ref": 6909, "role": "outer", "type": "way"},
                    {"ref": 6355, "role": "outer", "type": "way"},
                    {"ref": 6910, "role": "outer", "type": "way"},
                    {"ref": 6911, "role": "outer", "type": "way"},
                    {"ref": 6912, "role": "outer", "type": "way"},
                ],
            },
        )

    def test_RelationGet_deprecated(self):
        self._session_mock(filenames=["test_relation_get.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.RelationGet(321)

    def test_relation_get_with_version(self):
        self._session_mock()
        result = self.api.relation_get(765, 2)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], self.api_base + "/api/0.6/relation/765/2")
        self.assertEqual(result["id"], 765)
        self.assertEqual(result["changeset"], 41378)
        self.assertEqual(result["user"], "metaodi")
        self.assertEqual(result["tag"]["source"], "test")

    def test_RelationGet_with_version_deprecated(self):
        self._session_mock(filenames=["test_relation_get_with_version.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.RelationGet(765, 2)

    def test_relation_create(self):
        self._session_mock(auth=True)
        self.api.changeset_create = mock.Mock(return_value=3333)
        self.api._CurrentChangesetId = 3333
        test_relation = {
            "tag": {"type": "test"},
            "member": [
                {"ref": 6908, "role": "outer", "type": "way"},
                {"ref": 6352, "role": "point", "type": "node"},
            ],
        }
        cs = self.api.changeset_create({"comment": "This is a test relation"})
        self.assertEqual(cs, 3333)
        result = self.api.relation_create(test_relation)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "PUT")
        self.assertEqual(args[1], self.api_base + "/api/0.6/relation/create")
        self.assertEqual(result["id"], 8989)
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["member"], test_relation["member"])
        self.assertEqual(result["tag"], test_relation["tag"])

    def test_RelationCreate_deprecated(self):
        self._session_mock(auth=True, filenames=["test_relation_create.xml"])
        self.api.changeset_create = mock.Mock(return_value=3333)
        self.api._CurrentChangesetId = 3333
        test_relation = {
            "tag": {"type": "test"},
            "member": [
                {"ref": 6908, "role": "outer", "type": "way"},
                {"ref": 6352, "role": "point", "type": "node"},
            ],
        }
        with self.assertWarns(DeprecationWarning):
            self.api.RelationCreate(test_relation)

    def test_relation_create_existing_node(self):
        self.api.changeset_create = mock.Mock(return_value=1111)
        self.api._CurrentChangesetId = 1111
        test_relation = {
            "id": 456,
            "tag": {"type": "test"},
            "member": [
                {"ref": 6908, "role": "outer", "type": "way"},
                {"ref": 6352, "role": "point", "type": "node"},
            ],
        }
        with self.assertRaisesRegex(
            osmapi.OsmTypeAlreadyExistsError, "This relation already exists"
        ):
            self.api.relation_create(test_relation)

    def test_relation_update(self):
        self._session_mock(auth=True)
        self.api.changeset_create = mock.Mock(return_value=3333)
        self.api._CurrentChangesetId = 3333
        test_relation = {
            "id": 8989,
            "tag": {"type": "test update"},
            "member": [{"ref": 6908, "role": "outer", "type": "way"}],
        }
        cs = self.api.changeset_create({"comment": "This is a test relation"})
        self.assertEqual(cs, 3333)
        result = self.api.relation_update(test_relation)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "PUT")
        self.assertEqual(args[1], self.api_base + "/api/0.6/relation/8989")
        self.assertEqual(result["id"], 8989)
        self.assertEqual(result["version"], 42)
        self.assertEqual(result["member"], test_relation["member"])
        self.assertEqual(result["tag"], test_relation["tag"])

    def test_RelationUpdate_deprecated(self):
        self._session_mock(auth=True, filenames=["test_relation_update.xml"])
        self.api.changeset_create = mock.Mock(return_value=3333)
        self.api._CurrentChangesetId = 3333
        test_relation = {
            "id": 8989,
            "tag": {"type": "test update"},
            "member": [{"ref": 6908, "role": "outer", "type": "way"}],
        }
        with self.assertWarns(DeprecationWarning):
            self.api.RelationUpdate(test_relation)

    def test_relation_delete(self):
        self._session_mock(auth=True)
        self.api.changeset_create = mock.Mock(return_value=3333)
        self.api._CurrentChangesetId = 3333
        test_relation = {"id": 8989}
        cs = self.api.changeset_create({"comment": "This is a test relation"})
        self.assertEqual(cs, 3333)
        result = self.api.relation_delete(test_relation)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "DELETE")
        self.assertEqual(args[1], self.api_base + "/api/0.6/relation/8989")
        self.assertEqual(result["id"], 8989)
        self.assertEqual(result["version"], 43)

    def test_RelationDelete_deprecated(self):
        self._session_mock(auth=True, filenames=["test_relation_delete.xml"])
        self.api.changeset_create = mock.Mock(return_value=3333)
        self.api._CurrentChangesetId = 3333
        test_relation = {"id": 8989}
        with self.assertWarns(DeprecationWarning):
            self.api.RelationDelete(test_relation)

    def test_relation_history(self):
        self._session_mock()
        result = self.api.relation_history(2470397)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], f"{self.api_base}/api/0.6/relation/2470397/history")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["id"], 2470397)
        self.assertEqual(result[1]["version"], 1)
        self.assertEqual(
            result[1]["tag"],
            {
                "restriction": "only_straight_on",
                "type": "restriction",
            },
        )
        self.assertEqual(result[2]["version"], 2)

    def test_RelationHistory_deprecated(self):
        self._session_mock(filenames=["test_relation_history.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.RelationHistory(2470397)

    def test_relation_relations(self):
        self._session_mock()
        result = self.api.relation_relations(1532552)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], f"{self.api_base}/api/0.6/relation/1532552/relations")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1532553)
        self.assertEqual(result[0]["version"], 85)
        self.assertEqual(len(result[0]["member"]), 120)
        self.assertEqual(result[0]["tag"]["type"], "network")
        self.assertEqual(result[0]["tag"]["name"], "Aargauischer Radroutennetz")

    def test_RelationRelations_deprecated(self):
        self._session_mock(filenames=["test_relation_relations.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.RelationRelations(1532552)

    def test_relation_relations_unused_element(self):
        self._session_mock()
        result = self.api.relation_relations(1532552)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], f"{self.api_base}/api/0.6/relation/1532552/relations")
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_relation_full(self):
        self._session_mock()
        result = self.api.relation_full(2470397)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], f"{self.api_base}/api/0.6/relation/2470397/full")
        self.assertEqual(len(result), 11)
        self.assertEqual(result[1]["data"]["id"], 101142277)
        self.assertEqual(result[1]["data"]["version"], 8)
        self.assertEqual(result[1]["type"], "node")
        self.assertEqual(result[10]["data"]["id"], 2470397)
        self.assertEqual(result[10]["data"]["version"], 2)
        self.assertEqual(result[10]["type"], "relation")

    def test_relations_get(self):
        self._session_mock()
        result = self.api.relations_get([1532552, 1532553])
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(
            args[1], f"{self.api_base}/api/0.6/relations?relations=1532552,1532553"
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1532553]["id"], 1532553)
        self.assertEqual(result[1532553]["version"], 85)
        self.assertEqual(result[1532553]["user"], "SimonPoole")
        self.assertEqual(result[1532552]["id"], 1532552)
        self.assertEqual(result[1532552]["visible"], True)
        self.assertEqual(result[1532552]["tag"]["route"], "bicycle")

    def test_RelationsGet_deprecated(self):
        self._session_mock(filenames=["test_relations_get.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.RelationsGet([1532552, 1532553])

    def test_RelationFull_with_deleted_relation(self):
        self._session_mock(filenames=[], status=410)

        with self.assertRaises(osmapi.ElementDeletedApiError) as context:
            self.api.relation_full(2911456)
        self.assertEqual(410, context.exception.status)

    def test_RelationFull_deprecated(self):
        self._session_mock(filenames=["test_relation_full.xml"])

        with self.assertWarns(DeprecationWarning):
            self.api.RelationFull(2911456)