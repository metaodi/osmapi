from __future__ import (unicode_literals, absolute_import)
from . import osmapi_test
import osmapi
import mock
import datetime


class TestOsmApiRelation(osmapi_test.TestOsmApi):
    def test_RelationGet(self):
        self._session_mock()

        result = self.api.RelationGet(321)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], self.api_base + '/api/0.6/relation/321')

        self.assertEqual(result, {
            'id': 321,
            'changeset': 434,
            'uid': 12,
            'timestamp': datetime.datetime(2009, 9, 15, 22, 24, 25),
            'visible': True,
            'version': 1,
            'user': 'green525',
            'tag': {
                'admin_level': '9',
                'boundary': 'administrative',
                'type': 'multipolygon',
            },
            'member': [
                {
                    'ref': 6908,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 6352,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 5669,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 5682,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 6909,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 6355,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 6910,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 6911,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 6912,
                    'role': 'outer',
                    'type': 'way'
                }
            ]
        })

    def test_RelationGet_with_version(self):
        self._session_mock()

        result = self.api.RelationGet(765, 2)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], self.api_base + '/api/0.6/relation/765/2')

        self.assertEqual(result['id'], 765)
        self.assertEqual(result['changeset'], 41378)
        self.assertEqual(result['user'], 'metaodi')
        self.assertEqual(result['tag']['source'], 'test')

    def test_RelationCreate(self):
        self._session_mock(auth=True)

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=3333
        )
        self.api._CurrentChangesetId = 3333

        test_relation = {
            'tag': {
                'type': 'test',
            },
            'member': [
                {
                    'ref': 6908,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 6352,
                    'role': 'point',
                    'type': 'node'
                },
            ]
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test relation'
        })
        self.assertEqual(cs, 3333)

        result = self.api.RelationCreate(test_relation)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertEqual(args[1], self.api_base + '/api/0.6/relation/create')

        self.assertEqual(result['id'], 8989)
        self.assertEqual(result['version'], 1)
        self.assertEqual(result['member'], test_relation['member'])
        self.assertEqual(result['tag'], test_relation['tag'])

    def test_RelationCreate_existing_node(self):
        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111

        test_relation = {
            'id': 456,
            'tag': {
                'type': 'test',
            },
            'member': [
                {
                    'ref': 6908,
                    'role': 'outer',
                    'type': 'way'
                },
                {
                    'ref': 6352,
                    'role': 'point',
                    'type': 'node'
                },
            ]
        }

        with self.assertRaisesRegex(
                osmapi.OsmTypeAlreadyExistsError,
                'This relation already exists'):
            self.api.RelationCreate(test_relation)

    def test_RelationUpdate(self):
        self._session_mock(auth=True)

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=3333
        )
        self.api._CurrentChangesetId = 3333

        test_relation = {
            'id': 8989,
            'tag': {
                'type': 'test update',
            },
            'member': [
                {
                    'ref': 6908,
                    'role': 'outer',
                    'type': 'way'
                }
            ]
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test relation'
        })
        self.assertEqual(cs, 3333)

        result = self.api.RelationUpdate(test_relation)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertEqual(args[1], self.api_base + '/api/0.6/relation/8989')

        self.assertEqual(result['id'], 8989)
        self.assertEqual(result['version'], 42)
        self.assertEqual(result['member'], test_relation['member'])
        self.assertEqual(result['tag'], test_relation['tag'])

    def test_RelationDelete(self):
        self._session_mock(auth=True)

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=3333
        )
        self.api._CurrentChangesetId = 3333

        test_relation = {
            'id': 8989
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test relation'
        })
        self.assertEqual(cs, 3333)

        result = self.api.RelationDelete(test_relation)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'DELETE')
        self.assertEqual(args[1], self.api_base + '/api/0.6/relation/8989')

        self.assertEqual(result['id'], 8989)
        self.assertEqual(result['version'], 43)

    def test_RelationHistory(self):
        self._session_mock()

        result = self.api.RelationHistory(2470397)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/relation/2470397/history'
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]['id'], 2470397)
        self.assertEqual(result[1]['version'], 1)
        self.assertEqual(
            result[1]['tag'], {
                'restriction': 'only_straight_on',
                'type': 'restriction',
            }
        )
        self.assertEqual(result[2]['version'], 2)

    def test_RelationRelations(self):
        self._session_mock()

        result = self.api.RelationRelations(1532552)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/relation/1532552/relations'
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 1532553)
        self.assertEqual(result[0]['version'], 85)
        self.assertEqual(len(result[0]['member']), 120)
        self.assertEqual(result[0]['tag']['type'], 'network')
        self.assertEqual(
            result[0]['tag']['name'],
            'Aargauischer Radroutennetz'
        )

    def test_RelationRelationsUnusedElement(self):
        self._session_mock()

        result = self.api.RelationRelations(1532552)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/relation/1532552/relations'
        )

        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_RelationFull(self):
        self._session_mock()

        result = self.api.RelationFull(2470397)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/relation/2470397/full'
        )

        self.assertEqual(len(result), 11)
        self.assertEqual(result[1]['data']['id'], 101142277)
        self.assertEqual(result[1]['data']['version'], 8)
        self.assertEqual(result[1]['type'], 'node')
        self.assertEqual(result[10]['data']['id'], 2470397)
        self.assertEqual(result[10]['data']['version'], 2)
        self.assertEqual(result[10]['type'], 'relation')

    def test_RelationsGet(self):
        self._session_mock()

        result = self.api.RelationsGet([1532552, 1532553])

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/relations?relations=1532552,1532553'
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[1532553]['id'], 1532553)
        self.assertEqual(result[1532553]['version'], 85)
        self.assertEqual(result[1532553]['user'], 'SimonPoole')
        self.assertEqual(result[1532552]['id'], 1532552)
        self.assertEqual(result[1532552]['visible'], True)
        self.assertEqual(result[1532552]['tag']['route'], 'bicycle')

    def test_RelationFull_with_deleted_relation(self):
        self._session_mock(filenames=[], status=410)

        with self.assertRaises(osmapi.ElementDeletedApiError) as context:
            self.api.RelationFull(2911456)
        self.assertEqual(410, context.exception.status)
