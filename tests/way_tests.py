from nose.tools import *  # noqa
import osmapi_tests
import mock


class TestOsmApiWay(osmapi_tests.TestOsmApi):
    def test_WayGet(self):
        self._http_mock()

        result = self.api.WayGet(321)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/way/321')

        assert_equals(result, {
            u'id': 321,
            u'changeset': 298,
            u'uid': 12,
            u'timestamp': u'2009-09-14T23:23:18Z',
            u'visible': True,
            u'version': 1,
            u'user': u'green525',
            u'tag': {
                u'admin_level': u'9',
                u'boundary': u'administrative',
            },
            u'nd': [
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
                11949
            ]
        })

    def test_WayGet_with_version(self):
        self._http_mock()

        result = self.api.WayGet(4294967296, 2)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/way/4294967296/2')

        assert_equals(result['id'], 4294967296)
        assert_equals(result['changeset'], 41303)
        assert_equals(result['user'], 'metaodi')

    def test_WayGet_nodata(self):
        self._http_mock()

        result = self.api.WayGet(321)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/way/321')

        assert_equals(result, '')

    def test_WayCreate(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=2222
        )
        self.api._CurrentChangesetId = 2222

        test_way = {
            'nd': [11949, 11950],
            'tag': {
                'highway': 'unclassified',
                'name': 'Osmapi Street'
            }
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test way'
        })
        assert_equals(cs, 2222)

        result = self.api.WayCreate(test_way)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'PUT')
        assert_equals(args[1], '/api/0.6/way/create')

        assert_equals(result['id'], 5454)
        assert_equals(result['nd'], test_way['nd'])
        assert_equals(result['tag'], test_way['tag'])

    def test_WayUpdate(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=2222
        )
        self.api._CurrentChangesetId = 2222

        test_way = {
            'id': 876,
            'nd': [11949, 11950],
            'tag': {
                'highway': 'unclassified',
                'name': 'Osmapi Street Update'
            }
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test way'
        })
        assert_equals(cs, 2222)

        result = self.api.WayUpdate(test_way)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'PUT')
        assert_equals(args[1], '/api/0.6/way/876')

        assert_equals(result['id'], 876)
        assert_equals(result['nd'], test_way['nd'])
        assert_equals(result['tag'], test_way['tag'])

    def test_WayDelete(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=2222
        )
        self.api._CurrentChangesetId = 2222

        test_way = {
            'id': 876
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test way delete'
        })
        assert_equals(cs, 2222)

        result = self.api.WayDelete(test_way)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'DELETE')
        assert_equals(args[1], '/api/0.6/way/876')
        assert_equals(result['id'], 876)

    def test_WayHistory(self):
        self._http_mock()

        result = self.api.WayHistory(4294967296)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/way/4294967296/history')

        assert_equals(len(result), 2)
        assert_equals(result[1]['id'], 4294967296)
        assert_equals(result[1]['version'], 1)
        assert_equals(
            result[1]['tag'], {
                'highway': 'unclassified',
                'name': 'Stansted Road',
            }
        )

    def test_WayRelations(self):
        self._http_mock()

        result = self.api.WayRelations(4295032193)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/way/4295032193/relations')

        assert_equals(len(result), 1)
        assert_equals(result[0]['id'], 4294968148)
        assert_equals(result[0]['changeset'], 23123)
        assert_equals(
            result[0]['member'][4],
            {
                'role': '',
                'ref': 4295032193,
                'type': 'way',
            }
        )
        assert_equals(
            result[0]['tag'],
            {
                'type': 'fancy',
            }
        )

    def test_WayFull(self):
        self._http_mock()

        result = self.api.WayFull(321)

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/way/321/full')

        assert_equals(len(result), 17)
        assert_equals(result[0]['data']['id'], 11949)
        assert_equals(result[0]['data']['changeset'], 298)
        assert_equals(result[0]['type'], 'node')
        assert_equals(result[16]['data']['id'], 321)
        assert_equals(result[16]['data']['changeset'], 298)
        assert_equals(result[16]['type'], 'way')

    def test_WaysGet(self):
        self._http_mock()

        result = self.api.WaysGet([456, 678])

        args, kwargs = self.api._http_request.call_args
        assert_equals(args[0], 'GET')
        assert_equals(args[1], '/api/0.6/ways?ways=456,678')

        assert_equals(len(result), 2)
        assert_is(type(result[456]), dict)
        assert_is(type(result[678]), dict)
        with self.assertRaises(KeyError):
            assert_is(type(result[123]), dict)
