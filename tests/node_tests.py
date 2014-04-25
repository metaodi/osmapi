from nose.tools import *  # noqa
import osmapi_tests
import mock
import osmapi


class TestOsmApiNode(osmapi_tests.TestOsmApi):
    def test_NodeGet(self):
        self._http_mock()

        result = self.api.NodeGet(123)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/node/123')

        assert_equals(result, {
            u'id': 123,
            u'changeset': 15293,
            u'uid': 605,
            u'timestamp': u'2012-04-18T11:14:26Z',
            u'lat': 51.8753146,
            u'lon': -1.4857118,
            u'visible': True,
            u'version': 8,
            u'user': u'freundchen',
            u'tag': {
                u'amenity': u'school',
                u'foo': u'bar',
                u'name': u'Berolina & Schule'
            },
        })

    def test_NodeGet_with_version(self):
        self._http_mock()

        result = self.api.NodeGet(123, NodeVersion=2)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/node/123/2')

        assert_equals(result, {
            u'id': 123,
            u'changeset': 4152,
            u'uid': 605,
            u'timestamp': u'2011-04-18T11:14:26Z',
            u'lat': 51.8753146,
            u'lon': -1.4857118,
            u'visible': True,
            u'version': 2,
            u'user': u'freundchen',
            u'tag': {
                u'amenity': u'school',
            },
        })

    def test_NodeCreate_wo_changeset(self):
        test_node = {
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'religion': 'pastafarian'
            }
        }

        try:
            with self.assertRaisesRegexp(
                    Exception,
                    'need to open a changeset'):
                self.api.NodeCreate(test_node)
        except AttributeError:  # block for Python 2.6
            try:
                self.api.NodeCreate(test_node)
            except Exception, message:
                self.failUnlessEqual(
                    message.args[0],
                    'You need to open a changeset before uploading data'
                )
            else:
                self.fail('Excpetion for missing changeset not raised')

    def test_NodeCreate_changesetauto(self):
        self.api = osmapi.OsmApi(
            api="api06.dev.openstreetmap.org",
            changesetauto=True
        )
        self._http_mock(destructor=False)

        test_node = {
            'lat': 47.123,
            'lon': 8.555,
            'tag': {
                'amenity': 'place_of_worship',
                'religion': 'pastafarian'
            }
        }

        assert_true(self.api.NodeCreate(test_node) is None)

    def test_NodeCreate(self):
        self._http_mock()

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
        assert_equals(cs, 1111)
        result = self.api.NodeCreate(test_node)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'PUT')
        assert_equals(args[1], '/api/0.6/node/create')

        assert_equals(result['id'], 9876)
        assert_equals(result['lat'], test_node['lat'])
        assert_equals(result['lon'], test_node['lon'])
        assert_equals(result['tag'], test_node['tag'])

    def test_NodeUpdate(self):
        self._http_mock()

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
        assert_equals(cs, 1111)
        result = self.api.NodeUpdate(test_node)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'PUT')
        assert_equals(args[1], '/api/0.6/node/7676')

        assert_equals(result['id'], 7676)
        assert_equals(result['lat'], test_node['lat'])
        assert_equals(result['lon'], test_node['lon'])
        assert_equals(result['tag'], test_node['tag'])

    def test_NodeDelete(self):
        self._http_mock()

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
        assert_equals(cs, 1111)

        result = self.api.NodeDelete(test_node)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'DELETE')
        assert_equals(args[1], '/api/0.6/node/7676')
        assert_equals(result['id'], 7676)

    def test_NodeHistory(self):
        self._http_mock()

        result = self.api.NodeHistory(123)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/node/123/history')

        assert_equals(len(result), 8)
        assert_equals(result[4]['id'], 123)
        assert_equals(result[4]['version'], 4)
        assert_equals(result[4]['lat'], 51.8753146)
        assert_equals(result[4]['lon'], -1.4857118)
        assert_equals(
            result[4]['tag'], {
                'empty': '',
                'foo': 'bar',
            }
        )

    def test_NodeWays(self):
        self._http_mock()

        result = self.api.NodeWays(234)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/node/234/ways')

        assert_equals(len(result), 1)
        assert_equals(result[0]['id'], 60)
        assert_equals(result[0]['changeset'], 61)
        assert_equals(
            result[0]['tag'],
            {
                'highway': 'path',
                'name': 'Dog walking path',
            }
        )

    def test_NodeRelations(self):
        self._http_mock()

        result = self.api.NodeRelations(4295668179)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/node/4295668179/relations')

        assert_equals(len(result), 1)
        assert_equals(result[0]['id'], 4294968148)
        assert_equals(result[0]['changeset'], 23123)
        assert_equals(
            result[0]['member'][1],
            {
                'role': 'point',
                'ref': 4295668179,
                'type': 'node',
            }
        )
        assert_equals(
            result[0]['tag'],
            {
                'type': 'fancy',
            }
        )

    def test_NodesGet(self):
        self._http_mock()

        result = self.api.NodesGet([123, 345])

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/nodes?nodes=123,345')

        assert_equals(len(result), 2)
        assert_equals(result[123], {
            u'id': 123,
            u'changeset': 15293,
            u'uid': 605,
            u'timestamp': u'2012-04-18T11:14:26Z',
            u'lat': 51.8753146,
            u'lon': -1.4857118,
            u'visible': True,
            u'version': 8,
            u'user': u'freundchen',
            u'tag': {
                u'amenity': u'school',
                u'foo': u'bar',
                u'name': u'Berolina & Schule'
            },
        })
        assert_equals(result[345], {
            u'id': 345,
            u'changeset': 244,
            u'timestamp': u'2009-09-12T03:22:59Z',
            u'uid': 1,
            u'visible': False,
            u'version': 2,
            u'user': u'guggis',
            u'tag': {},
        })
