from nose.tools import *  # noqa
import osmapi_tests
import mock


def debug(result):
    from pprint import pprint
    pprint(result)
    assert_equals(0, 1)


class TestOsmApiRelation(osmapi_tests.TestOsmApi):
    def test_RelationGet(self):
        self._http_mock()

        result = self.api.RelationGet(321)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/relation/321')

        self.assertEquals(result, {
            u'id': 321,
            u'changeset': 434,
            u'uid': 12,
            u'timestamp': u'2009-09-15T22:24:25Z',
            u'visible': True,
            u'version': 1,
            u'user': u'green525',
            u'tag': {
                u'admin_level': u'9',
                u'boundary': u'administrative',
                u'type': u'multipolygon',
            },
            u'member': [
                {
                    u'ref': 6908,
                    u'role': u'outer',
                    u'type': u'way'
                },
                {
                    u'ref': 6352,
                    u'role': u'outer',
                    u'type': u'way'
                },
                {
                    u'ref': 5669,
                    u'role': u'outer',
                    u'type': u'way'
                },
                {
                    u'ref': 5682,
                    u'role': u'outer',
                    u'type': u'way'
                },
                {
                    u'ref': 6909,
                    u'role': u'outer',
                    u'type': u'way'
                },
                {
                    u'ref': 6355,
                    u'role': u'outer',
                    u'type': u'way'
                },
                {
                    u'ref': 6910,
                    u'role': u'outer',
                    u'type': u'way'
                },
                {
                    u'ref': 6911,
                    u'role': u'outer',
                    u'type': u'way'
                },
                {
                    u'ref': 6912,
                    u'role': u'outer',
                    u'type': u'way'
                }
            ]
        })

    def test_RelationGet_with_version(self):
        self._http_mock()

        result = self.api.RelationGet(765, 2)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/relation/765/2')

        self.assertEquals(result['id'], 765)
        self.assertEquals(result['changeset'], 41378)
        self.assertEquals(result['user'], 'metaodi')
        self.assertEquals(result['tag']['source'], 'test')

    def test_RelationCreate(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=3333
        )
        self.api._CurrentChangesetId = 3333

        test_relation = {
            u'tag': {
                u'type': u'test',
            },
            u'member': [
                {
                    u'ref': 6908,
                    u'role': u'outer',
                    u'type': u'way'
                },
                {
                    u'ref': 6352,
                    u'role': u'point',
                    u'type': u'node'
                },
            ]
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test relation'
        })
        self.assertEquals(cs, 3333)

        result = self.api.RelationCreate(test_relation)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], '/api/0.6/relation/create')

        self.assertEquals(result['id'], 8989)
        self.assertEquals(result['version'], 1)
        self.assertEquals(result['member'], test_relation['member'])
        self.assertEquals(result['tag'], test_relation['tag'])

    def test_RelationUpdate(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=3333
        )
        self.api._CurrentChangesetId = 3333

        test_relation = {
            u'id': 8989,
            u'tag': {
                u'type': u'test update',
            },
            u'member': [
                {
                    u'ref': 6908,
                    u'role': u'outer',
                    u'type': u'way'
                }
            ]
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test relation'
        })
        self.assertEquals(cs, 3333)

        result = self.api.RelationUpdate(test_relation)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], '/api/0.6/relation/8989')

        self.assertEquals(result['id'], 8989)
        self.assertEquals(result['version'], 42)
        self.assertEquals(result['member'], test_relation['member'])
        self.assertEquals(result['tag'], test_relation['tag'])

    def test_RelationDelete(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=3333
        )
        self.api._CurrentChangesetId = 3333

        test_relation = {
            u'id': 8989
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test relation'
        })
        self.assertEquals(cs, 3333)

        result = self.api.RelationDelete(test_relation)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'DELETE')
        self.assertEquals(args[1], '/api/0.6/relation/8989')

        self.assertEquals(result['id'], 8989)
        self.assertEquals(result['version'], 43)

    def test_RelationHistory(self):
        self._http_mock()

        result = self.api.RelationHistory(2470397)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/relation/2470397/history')

        self.assertEquals(len(result), 2)
        self.assertEquals(result[1]['id'], 2470397)
        self.assertEquals(result[1]['version'], 1)
        self.assertEquals(
            result[1]['tag'], {
                'restriction': 'only_straight_on',
                'type': 'restriction',
            }
        )
        self.assertEquals(result[2]['version'], 2)

    def test_RelationRelations(self):
        self._http_mock()

        result = self.api.RelationRelations(1532552)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/relation/1532552/relations')

        self.assertEquals(len(result), 1)
        self.assertEquals(result[0]['id'], 1532553)
        self.assertEquals(result[0]['version'], 85)
        self.assertEquals(len(result[0]['member']), 120)
        self.assertEquals(result[0]['tag']['type'], 'network')
        self.assertEquals(
            result[0]['tag']['name'],
            'Aargauischer Radroutennetz'
        )

    def test_RelationFull(self):
        self._http_mock()

        result = self.api.RelationFull(2470397)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/relation/2470397/full')

        self.assertEquals(len(result), 11)
        self.assertEquals(result[1]['data']['id'], 101142277)
        self.assertEquals(result[1]['data']['version'], 8)
        self.assertEquals(result[1]['type'], 'node')
        self.assertEquals(result[10]['data']['id'], 2470397)
        self.assertEquals(result[10]['data']['version'], 2)
        self.assertEquals(result[10]['type'], 'relation')

    def test_RelationsGet(self):
        self._http_mock()

        result = self.api.RelationsGet([1532552, 1532553])

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(
            args[1],
            '/api/0.6/relations?relations=1532552,1532553'
        )

        self.assertEquals(len(result), 2)
        self.assertEquals(result[1532553]['id'], 1532553)
        self.assertEquals(result[1532553]['version'], 85)
        self.assertEquals(result[1532553]['user'], 'SimonPoole')
        self.assertEquals(result[1532552]['id'], 1532552)
        self.assertEquals(result[1532552]['visible'], True)
        self.assertEquals(result[1532552]['tag']['route'], 'bicycle')
