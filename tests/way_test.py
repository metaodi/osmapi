from . import osmapi_test
import osmapi
from unittest import mock
import datetime


class TestOsmApiWay(osmapi_test.TestOsmApi):
    def test_way_get(self):
        self._session_mock()
        result = self.api.way_get(321)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], self.api_base + "/api/0.6/way/321")
        self.assertEqual(
            result,
            {
                "id": 321,
                "changeset": 298,
                "uid": 12,
                "timestamp": datetime.datetime(2009, 9, 14, 23, 23, 18),
                "visible": True,
                "version": 1,
                "user": "green525",
                "tag": {
                    "admin_level": "9",
                    "boundary": "administrative",
                },
                "nd": [
                    11949,
                    11950,
                    11951,
                    11952,
                    11953,
                    11954,
                    11955,
                    11956,
                    11957,
                    11958,
                    11959,
                    11960,
                    11961,
                    11962,
                    11963,
                    11964,
                    11949,
                ],
            },
        )

    def test_WayGet_deprecated(self):
        self._session_mock(filenames=["test_way_get.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.WayGet(321)

    def test_way_get_with_version(self):
        self._session_mock()
        result = self.api.way_get(4294967296, 2)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], f"{self.api_base}/api/0.6/way/4294967296/2")
        self.assertEqual(result["id"], 4294967296)
        self.assertEqual(result["changeset"], 41303)
        self.assertEqual(result["user"], "metaodi")

    def test_WayGet_with_version_deprecated(self):
        self._session_mock(filenames=["test_way_get_with_version.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.WayGet(4294967296, 2)

    def test_way_get_nodata(self):
        self._session_mock()
        with self.assertRaises(osmapi.ResponseEmptyApiError):
            self.api.way_get(321)

    def test_way_create(self):
        self._session_mock(auth=True)
        self.api.changeset_create = mock.Mock(return_value=2222)
        self.api._current_changeset_id = 2222
        test_way = {
            "nd": [11949, 11950],
            "tag": {"highway": "unclassified", "name": "Osmapi Street"},
        }
        cs = self.api.changeset_create({"comment": "This is a test way"})
        self.assertEqual(cs, 2222)
        result = self.api.way_create(test_way)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "PUT")
        self.assertEqual(args[1], self.api_base + "/api/0.6/way/create")
        self.assertEqual(result["id"], 5454)
        self.assertEqual(result["nd"], test_way["nd"])
        self.assertEqual(result["tag"], test_way["tag"])

    def test_WayCreate_deprecated(self):
        self._session_mock(auth=True, filenames=["test_way_create.xml"])
        self.api.changeset_create = mock.Mock(return_value=2222)
        self.api._current_changeset_id = 2222
        test_way = {
            "nd": [11949, 11950],
            "tag": {"highway": "unclassified", "name": "Osmapi Street"},
        }
        with self.assertWarns(DeprecationWarning):
            self.api.WayCreate(test_way)

    def test_way_create_existing_node(self):
        self.api.changeset_create = mock.Mock(return_value=1111)
        self.api._current_changeset_id = 1111
        test_way = {
            "id": 456,
            "nd": [11949, 11950],
            "tag": {"highway": "unclassified", "name": "Osmapi Street"},
        }
        with self.assertRaisesRegex(
            osmapi.OsmTypeAlreadyExistsError, "This way already exists"
        ):
            self.api.way_create(test_way)

    def test_way_update(self):
        self._session_mock(auth=True)
        self.api.changeset_create = mock.Mock(return_value=2222)
        self.api._current_changeset_id = 2222
        test_way = {
            "id": 876,
            "nd": [11949, 11950],
            "tag": {"highway": "unclassified", "name": "Osmapi Street Update"},
        }
        cs = self.api.changeset_create({"comment": "This is a test way"})
        self.assertEqual(cs, 2222)
        result = self.api.way_update(test_way)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "PUT")
        self.assertEqual(args[1], self.api_base + "/api/0.6/way/876")
        self.assertEqual(result["id"], 876)
        self.assertEqual(result["version"], 7)
        self.assertEqual(result["nd"], test_way["nd"])
        self.assertEqual(result["tag"], test_way["tag"])

    def test_WayUpdate_deprecated(self):
        self._session_mock(auth=True, filenames=["test_way_update.xml"])
        self.api.changeset_create = mock.Mock(return_value=2222)
        self.api._current_changeset_id = 2222
        test_way = {
            "id": 876,
            "nd": [11949, 11950],
            "tag": {"highway": "unclassified", "name": "Osmapi Street Update"},
        }
        with self.assertWarns(DeprecationWarning):
            self.api.WayUpdate(test_way)

    def test_way_update_precondition_failed(self):
        self._session_mock(auth=True, status=412)
        self.api.changeset_create = mock.Mock(return_value=1111)
        self.api._current_changeset_id = 1111
        test_way = {
            "id": 876,
            "nd": [11949, 11950],
            "tag": {"highway": "unclassified", "name": "Osmapi Street Update"},
        }
        self.api.changeset_create({"comment": "This is a test dataset"})
        with self.assertRaises(osmapi.PreconditionFailedApiError) as cm:
            self.api.way_update(test_way)
        self.assertEqual(cm.exception.status, 412)
        self.assertEqual(
            cm.exception.payload,
            (
                "Way 876 requires the nodes with id in (11950), "
                "which either do not exist, or are not visible."
            ),
        )

    def test_way_delete(self):
        self._session_mock(auth=True)
        self.api.changeset_create = mock.Mock(return_value=2222)
        self.api._current_changeset_id = 2222
        test_way = {"id": 876}
        cs = self.api.changeset_create({"comment": "This is a test way delete"})
        self.assertEqual(cs, 2222)
        result = self.api.way_delete(test_way)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "DELETE")
        self.assertEqual(args[1], self.api_base + "/api/0.6/way/876")
        self.assertEqual(result["id"], 876)
        self.assertEqual(result["version"], 8)

    def test_WayDelete_deprecated(self):
        self._session_mock(auth=True, filenames=["test_way_delete.xml"])
        self.api.changeset_create = mock.Mock(return_value=2222)
        self.api._current_changeset_id = 2222
        test_way = {"id": 876}
        with self.assertWarns(DeprecationWarning):
            self.api.WayDelete(test_way)

    def test_way_history(self):
        self._session_mock()
        result = self.api.way_history(4294967296)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], f"{self.api_base}/api/0.6/way/4294967296/history")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["id"], 4294967296)
        self.assertEqual(result[1]["version"], 1)
        self.assertEqual(
            result[1]["tag"],
            {
                "highway": "unclassified",
                "name": "Stansted Road",
            },
        )

    def test_WayHistory_deprecated(self):
        self._session_mock(filenames=["test_way_history.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.WayHistory(4294967296)

    def test_way_relations(self):
        self._session_mock()
        result = self.api.way_relations(4295032193)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], f"{self.api_base}/api/0.6/way/4295032193/relations")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 4294968148)
        self.assertEqual(result[0]["changeset"], 23123)
        self.assertEqual(
            result[0]["member"][4],
            {
                "role": "",
                "ref": 4295032193,
                "type": "way",
            },
        )
        self.assertEqual(
            result[0]["tag"],
            {
                "type": "fancy",
            },
        )

    def test_WayRelations_deprecated(self):
        self._session_mock(filenames=["test_way_relations.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.WayRelations(4295032193)

    def test_way_relations_unused_element(self):
        self._session_mock()
        result = self.api.way_relations(4295032193)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], self.api_base + "/api/0.6/way/4295032193/relations")
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_way_full(self):
        self._session_mock()
        result = self.api.way_full(321)
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], self.api_base + "/api/0.6/way/321/full")
        self.assertEqual(len(result), 17)
        self.assertEqual(result[0]["data"]["id"], 11949)
        self.assertEqual(result[0]["data"]["changeset"], 298)
        self.assertEqual(result[0]["type"], "node")
        self.assertEqual(result[16]["data"]["id"], 321)
        self.assertEqual(result[16]["data"]["changeset"], 298)
        self.assertEqual(result[16]["type"], "way")

    def test_WayFull_deprecated(self):
        self._session_mock(filenames=["test_way_full.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.WayFull(321)

    def test_way_full_invalid_response(self):
        self._session_mock()
        with self.assertRaises(osmapi.XmlResponseInvalidError):
            self.api.way_full(321)

    def test_ways_get(self):
        self._session_mock()
        result = self.api.ways_get([456, 678])
        args, kwargs = self.session_mock.request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], f"{self.api_base}/api/0.6/ways?ways=456,678")
        self.assertEqual(len(result), 2)
        self.assertIs(type(result[456]), dict)
        self.assertIs(type(result[678]), dict)
        with self.assertRaises(KeyError):
            self.assertIs(type(result[123]), dict)

    def test_WaysGet_deprecated(self):
        self._session_mock(filenames=["test_ways_get.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.WaysGet([456, 678])
