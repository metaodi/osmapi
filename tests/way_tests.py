from __future__ import (unicode_literals, absolute_import)
from nose.tools import *  # noqa
from . import osmapi_tests
import mock
import datetime


class TestOsmApiWay(osmapi_tests.TestOsmApi):
    def test_WayGet(self):
        self._conn_mock()

        result = self.api.WayGet(321)

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/way/321')

        self.assertEquals(result, {
            'id': 321,
            'changeset': 298,
            'uid': 12,
            'timestamp': datetime.datetime(2009, 9, 14, 23, 23, 18),
            'visible': True,
            'version': 1,
            'user': 'green525',
            'tag': {
                'admin_level': '9',
                'boundary': 'administrative',
            },
            'nd': [
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
        self._conn_mock()

        result = self.api.WayGet(4294967296, 2)

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/way/4294967296/2')

        self.assertEquals(result['id'], 4294967296)
        self.assertEquals(result['changeset'], 41303)
        self.assertEquals(result['user'], 'metaodi')

    def test_WayGet_nodata(self):
        self._conn_mock()

        result = self.api.WayGet(321)

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/way/321')

        self.assertEquals(result, '')

    def test_WayCreate(self):
        self._conn_mock(auth=True)

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
        self.assertEquals(cs, 2222)

        result = self.api.WayCreate(test_way)

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], '/api/0.6/way/create')

        self.assertEquals(result['id'], 5454)
        self.assertEquals(result['nd'], test_way['nd'])
        self.assertEquals(result['tag'], test_way['tag'])

    def test_WayUpdate(self):
        self._conn_mock(auth=True)

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
        self.assertEquals(cs, 2222)

        result = self.api.WayUpdate(test_way)

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], '/api/0.6/way/876')

        self.assertEquals(result['id'], 876)
        self.assertEquals(result['version'], 7)
        self.assertEquals(result['nd'], test_way['nd'])
        self.assertEquals(result['tag'], test_way['tag'])

    def test_WayDelete(self):
        self._conn_mock(auth=True)

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
        self.assertEquals(cs, 2222)

        result = self.api.WayDelete(test_way)

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'DELETE')
        self.assertEquals(args[1], '/api/0.6/way/876')
        self.assertEquals(result['id'], 876)
        self.assertEquals(result['version'], 8)

    def test_WayHistory(self):
        self._conn_mock()

        result = self.api.WayHistory(4294967296)

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/way/4294967296/history')

        self.assertEquals(len(result), 2)
        self.assertEquals(result[1]['id'], 4294967296)
        self.assertEquals(result[1]['version'], 1)
        self.assertEquals(
            result[1]['tag'], {
                'highway': 'unclassified',
                'name': 'Stansted Road',
            }
        )

    def test_WayRelations(self):
        self._conn_mock()

        result = self.api.WayRelations(4295032193)

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/way/4295032193/relations')

        self.assertEquals(len(result), 1)
        self.assertEquals(result[0]['id'], 4294968148)
        self.assertEquals(result[0]['changeset'], 23123)
        self.assertEquals(
            result[0]['member'][4],
            {
                'role': '',
                'ref': 4295032193,
                'type': 'way',
            }
        )
        self.assertEquals(
            result[0]['tag'],
            {
                'type': 'fancy',
            }
        )

    def test_WayFull(self):
        self._conn_mock()

        result = self.api.WayFull(321)

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/way/321/full')

        self.assertEquals(len(result), 17)
        self.assertEquals(result[0]['data']['id'], 11949)
        self.assertEquals(result[0]['data']['changeset'], 298)
        self.assertEquals(result[0]['type'], 'node')
        self.assertEquals(result[16]['data']['id'], 321)
        self.assertEquals(result[16]['data']['changeset'], 298)
        self.assertEquals(result[16]['type'], 'way')

    def test_WaysGet(self):
        self._conn_mock()

        result = self.api.WaysGet([456, 678])

        args, kwargs = self.api._conn.putrequest.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/ways?ways=456,678')

        self.assertEquals(len(result), 2)
        self.assertIs(type(result[456]), dict)
        self.assertIs(type(result[678]), dict)
        with self.assertRaises(KeyError):
            self.assertIs(type(result[123]), dict)
