from __future__ import (unicode_literals, absolute_import)
from . import osmapi_test
import osmapi
import mock
import datetime


class TestOsmApiNode(osmapi_test.TestOsmApi):
    def test_NodeGet(self):
        self._session_mock()

        result = self.api.NodeGet(123)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], self.api_base + '/api/0.6/node/123')

        self.assertEqual(result, {
            'id': 123,
            'changeset': 15293,
            'uid': 605,
            'timestamp': datetime.datetime(2012, 4, 18, 11, 14, 26),
            'lat': 51.8753146,
            'lon': -1.4857118,
            'visible': True,
            'version': 8,
            'user': 'freundchen',
            'tag': {
                'amenity': 'school',
                'foo': 'bar',
                'name': 'Berolina & Schule'
            },
        })

    def test_NodeGet_with_version(self):
        self._session_mock()

        result = self.api.NodeGet(123, NodeVersion=2)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], self.api_base + '/api/0.6/node/123/2')

        self.assertEqual(result, {
            'id': 123,
            'changeset': 4152,
            'uid': 605,
            'timestamp': datetime.datetime(2011, 4, 18, 11, 14, 26),
            'lat': 51.8753146,
            'lon': -1.4857118,
            'visible': True,
            'version': 2,
            'user': 'freundchen',
            'tag': {
                'amenity': 'school',
            },
        })

    def test_NodeGet_invalid_response(self):
        self._session_mock()

        with self.assertRaises(osmapi.XmlResponseInvalidError):
            self.api.NodeGet(987)

    def test_NodeCreate_changesetauto(self):
        # setup mock
        self.api = osmapi.OsmApi(
            api="api06.dev.openstreetmap.org",
            changesetauto=True
        )
        for filename in ['test_NodeCreate_changesetauto.xml',
                         'test_ChangesetUpload_create_node.xml',
                         'test_ChangesetClose.xml']:
            self._session_mock(auth=True, filenames=[filename])

            test_node = {
                'lat': 47.123,
                'lon': 8.555,
                'tag': {
                    'amenity': 'place_of_worship',
                    'religion': 'pastafarian'
                }
            }

            self.assertIsNone(self.api.NodeCreate(test_node))

    def test_NodeCreate(self):
        self._session_mock(auth=True)

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111

        test_node = {
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'religion': 'pastafarian'
            }
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test dataset'
        })
        self.assertEqual(cs, 1111)
        result = self.api.NodeCreate(test_node)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertEqual(args[1], self.api_base + '/api/0.6/node/create')

        self.assertEqual(result['id'], 9876)
        self.assertEqual(result['lat'], test_node['lat'])
        self.assertEqual(result['lon'], test_node['lon'])
        self.assertEqual(result['tag'], test_node['tag'])

    def test_NodeCreate_wo_changeset(self):
        test_node = {
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'religion': 'pastafarian'
            }
        }

        with self.assertRaisesRegex(
                osmapi.NoChangesetOpenError,
                'need to open a changeset'):
            self.api.NodeCreate(test_node)

    def test_NodeCreate_existing_node(self):
        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111

        test_node = {
            'id': 123,
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'religion': 'pastafarian'
            }
        }

        with self.assertRaisesRegex(
                osmapi.OsmTypeAlreadyExistsError,
                'This node already exists'):
            self.api.NodeCreate(test_node)

    def test_NodeCreate_wo_auth(self):
        self._session_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111
        test_node = {
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'religion': 'pastafarian'
            }
        }

        with self.assertRaisesRegex(
                osmapi.UsernamePasswordMissingError,
                'Username/Password missing'):
            self.api.NodeCreate(test_node)

    def test_NodeCreate_with_exception(self):
        self._session_mock(auth=True)
        self.api._http_request = mock.Mock(side_effect=Exception)

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111
        test_node = {
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'religion': 'pastafarian'
            }
        }

        with self.assertRaisesRegex(
                osmapi.MaximumRetryLimitReachedError,
                'Give up after 5 retries'):
            self.api.NodeCreate(test_node)

    def test_NodeUpdate(self):
        self._session_mock(auth=True)

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111

        test_node = {
            'id': 7676,
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'name': 'christian'
            }
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test dataset'
        })
        self.assertEqual(cs, 1111)
        result = self.api.NodeUpdate(test_node)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertEqual(args[1], self.api_base + '/api/0.6/node/7676')

        self.assertEqual(result['id'], 7676)
        self.assertEqual(result['version'], 3)
        self.assertEqual(result['lat'], test_node['lat'])
        self.assertEqual(result['lon'], test_node['lon'])
        self.assertEqual(result['tag'], test_node['tag'])

    def test_NodeUpdateWhenChangesetIsClosed(self):
        self._session_mock(auth=True, status=409)

        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111

        test_node = {
            'id': 7676,
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'name': 'christian'
            }
        }

        self.api.ChangesetCreate({
            'comment': 'This is a test dataset'
        })

        with self.assertRaises(osmapi.ChangesetClosedApiError) as cm:
            self.api.NodeUpdate(test_node)

        self.assertEqual(cm.exception.status, 409)
        self.assertEqual(
            cm.exception.payload,
            "The changeset 2222 was closed at 2021-11-20 09:42:47 UTC."
        )

    def test_NodeUpdateConflict(self):
        self._session_mock(auth=True, status=409)

        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111

        test_node = {
            'id': 7676,
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'name': 'christian'
            }
        }

        self.api.ChangesetCreate({
            'comment': 'This is a test dataset'
        })

        with self.assertRaises(osmapi.VersionMismatchApiError) as cm:
            self.api.NodeUpdate(test_node)

        self.assertEqual(cm.exception.status, 409)
        self.assertEqual(
            cm.exception.payload,
            "Version does not match the current database version of the element"
        )

    def test_NodeDelete(self):
        self._session_mock(auth=True)

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111

        test_node = {
            'id': 7676
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test dataset'
        })
        self.assertEqual(cs, 1111)

        result = self.api.NodeDelete(test_node)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'DELETE')
        self.assertEqual(args[1], self.api_base + '/api/0.6/node/7676')
        self.assertEqual(result['id'], 7676)
        self.assertEqual(result['version'], 4)

    def test_NodeHistory(self):
        self._session_mock()

        result = self.api.NodeHistory(123)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], self.api_base + '/api/0.6/node/123/history')

        self.assertEqual(len(result), 8)
        self.assertEqual(result[4]['id'], 123)
        self.assertEqual(result[4]['version'], 4)
        self.assertEqual(result[4]['lat'], 51.8753146)
        self.assertEqual(result[4]['lon'], -1.4857118)
        self.assertEqual(
            result[4]['tag'], {
                'empty': '',
                'foo': 'bar',
            }
        )

    def test_NodeWays(self):
        self._session_mock()

        result = self.api.NodeWays(234)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], self.api_base + '/api/0.6/node/234/ways')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 60)
        self.assertEqual(result[0]['changeset'], 61)
        self.assertEqual(
            result[0]['tag'],
            {
                'highway': 'path',
                'name': 'Dog walking path',
            }
        )

    def test_NodeWaysNotExists(self):
        self._session_mock()

        result = self.api.NodeWays(404)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], f'{self.api_base}/api/0.6/node/404/ways')

        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_NodeRelations(self):
        self._session_mock()

        result = self.api.NodeRelations(4295668179)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/node/4295668179/relations'
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 4294968148)
        self.assertEqual(result[0]['changeset'], 23123)
        self.assertEqual(
            result[0]['member'][1],
            {
                'role': 'point',
                'ref': 4295668179,
                'type': 'node',
            }
        )
        self.assertEqual(
            result[0]['tag'],
            {
                'type': 'fancy',
            }
        )

    def test_NodeRelationsUnusedElement(self):
        self._session_mock()

        result = self.api.NodeRelations(4295668179)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            self.api_base + '/api/0.6/node/4295668179/relations'
        )

        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_NodesGet(self):
        self._session_mock()

        result = self.api.NodesGet([123, 345])

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/nodes?nodes=123,345'
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[123], {
            'id': 123,
            'changeset': 15293,
            'uid': 605,
            'timestamp': datetime.datetime(2012, 4, 18, 11, 14, 26),
            'lat': 51.8753146,
            'lon': -1.4857118,
            'visible': True,
            'version': 8,
            'user': 'freundchen',
            'tag': {
                'amenity': 'school',
                'foo': 'bar',
                'name': 'Berolina & Schule'
            },
        })
        self.assertEqual(result[345], {
            'id': 345,
            'changeset': 244,
            'timestamp': datetime.datetime(2009, 9, 12, 3, 22, 59),
            'uid': 1,
            'visible': False,
            'version': 2,
            'user': 'guggis',
            'tag': {},
        })
