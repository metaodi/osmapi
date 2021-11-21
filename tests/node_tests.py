from __future__ import (unicode_literals, absolute_import)
from . import osmapi_tests
import osmapi
import mock
import datetime


class TestOsmApiNode(osmapi_tests.TestOsmApi):
    def test_NodeGet(self):
        self._session_mock()

        result = self.api.NodeGet(123)

        args, kwargs = self.api._session.request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], self.api_base + '/api/0.6/node/123')

        self.assertEquals(result, {
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
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], self.api_base + '/api/0.6/node/123/2')

        self.assertEquals(result, {
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
        self.assertEquals(cs, 1111)
        result = self.api.NodeCreate(test_node)

        args, kwargs = self.api._session.request.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], self.api_base + '/api/0.6/node/create')

        self.assertEquals(result['id'], 9876)
        self.assertEquals(result['lat'], test_node['lat'])
        self.assertEquals(result['lon'], test_node['lon'])
        self.assertEquals(result['tag'], test_node['tag'])

    def test_NodeCreate_wo_changeset(self):
        test_node = {
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'religion': 'pastafarian'
            }
        }

        with self.assertRaisesRegexp(
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

        with self.assertRaisesRegexp(
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

        with self.assertRaisesRegexp(
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

        with self.assertRaisesRegexp(
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
        self.assertEquals(cs, 1111)
        result = self.api.NodeUpdate(test_node)

        args, kwargs = self.api._session.request.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], self.api_base + '/api/0.6/node/7676')

        self.assertEquals(result['id'], 7676)
        self.assertEquals(result['version'], 3)
        self.assertEquals(result['lat'], test_node['lat'])
        self.assertEquals(result['lon'], test_node['lon'])
        self.assertEquals(result['tag'], test_node['tag'])

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

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test dataset'
        })

        with self.assertRaises(osmapi.ChangesetClosedApiError) as cm:
            result = self.api.NodeUpdate(test_node)

        self.assertEquals(cm.exception.status, 409)
        self.assertEquals(
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

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test dataset'
        })

        with self.assertRaises(osmapi.VersionMismatchApiError) as cm:
            result = self.api.NodeUpdate(test_node)

        self.assertEquals(cm.exception.status, 409)
        self.assertEquals(
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
        self.assertEquals(cs, 1111)

        result = self.api.NodeDelete(test_node)

        args, kwargs = self.api._session.request.call_args
        self.assertEquals(args[0], 'DELETE')
        self.assertEquals(args[1], self.api_base + '/api/0.6/node/7676')
        self.assertEquals(result['id'], 7676)
        self.assertEquals(result['version'], 4)

    def test_NodeHistory(self):
        self._session_mock()

        result = self.api.NodeHistory(123)

        args, kwargs = self.api._session.request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], self.api_base + '/api/0.6/node/123/history')

        self.assertEquals(len(result), 8)
        self.assertEquals(result[4]['id'], 123)
        self.assertEquals(result[4]['version'], 4)
        self.assertEquals(result[4]['lat'], 51.8753146)
        self.assertEquals(result[4]['lon'], -1.4857118)
        self.assertEquals(
            result[4]['tag'], {
                'empty': '',
                'foo': 'bar',
            }
        )

    def test_NodeWays(self):
        self._session_mock()

        result = self.api.NodeWays(234)

        args, kwargs = self.api._session.request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], self.api_base + '/api/0.6/node/234/ways')

        self.assertEquals(len(result), 1)
        self.assertEquals(result[0]['id'], 60)
        self.assertEquals(result[0]['changeset'], 61)
        self.assertEquals(
            result[0]['tag'],
            {
                'highway': 'path',
                'name': 'Dog walking path',
            }
        )

    def test_NodeRelations(self):
        self._session_mock()

        result = self.api.NodeRelations(4295668179)

        args, kwargs = self.api._session.request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1],
                          self.api_base + '/api/0.6/node/4295668179/relations')

        self.assertEquals(len(result), 1)
        self.assertEquals(result[0]['id'], 4294968148)
        self.assertEquals(result[0]['changeset'], 23123)
        self.assertEquals(
            result[0]['member'][1],
            {
                'role': 'point',
                'ref': 4295668179,
                'type': 'node',
            }
        )
        self.assertEquals(
            result[0]['tag'],
            {
                'type': 'fancy',
            }
        )

    def test_NodesGet(self):
        self._session_mock()

        result = self.api.NodesGet([123, 345])

        args, kwargs = self.api._session.request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1],
                          self.api_base + '/api/0.6/nodes?nodes=123,345')

        self.assertEquals(len(result), 2)
        self.assertEquals(result[123], {
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
        self.assertEquals(result[345], {
            'id': 345,
            'changeset': 244,
            'timestamp': datetime.datetime(2009, 9, 12, 3, 22, 59),
            'uid': 1,
            'visible': False,
            'version': 2,
            'user': 'guggis',
            'tag': {},
        })
