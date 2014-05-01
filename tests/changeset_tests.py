
from nose.tools import *  # noqa
import osmapi_tests
import mock


def debug(result):
    from pprint import pprint
    pprint(result)
    assert_equals(0, 1)


class TestOsmApiChangeset(osmapi_tests.TestOsmApi):
    def test_ChangesetGet(self):
        self._http_mock()

        result = self.api.ChangesetGet(123)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/changeset/123')
        self.assertFalse(args[2])

        self.assertEquals(result, {
            u'id': 123,
            u'closed_at': u'2009-09-07T22:57:37Z',
            u'created_at': u'2009-09-07T21:57:36Z',
            u'max_lat': u'52.4710193',
            u'max_lon': u'-1.4831815',
            u'min_lat': u'45.9667901',
            u'min_lon': u'-1.4998534',
            u'open': False,
            u'user': u'randomjunk',
            u'uid': 3,
            u'tag': {
                u'comment': u'correct node bug',
                u'created_by': u'Potlatch 1.2a',
            },
        })

    def test_ChangesetUpdate(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=4444
        )
        self.api._CurrentChangesetId = 4444

        result = self.api.ChangesetUpdate(
            {
                'test': 'foobar'
            }
        )

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], '/api/0.6/changeset/4444')
        self.assertTrue(args[2])
        self.assertEquals(
            args[3],
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<osm version="0.6" generator="osmapi/0.2.25">\n'
                '  <changeset visible="true">\n'
                '    <tag k="test" v="foobar"/>\n'
                '    <tag k="created_by" v="osmapi/0.2.25"/>\n'
                '  </changeset>\n'
                '</osm>\n'
            )
        )
        self.assertEquals(result, 4444)

    def test_ChangesetUpdate_with_created_by(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=4444
        )
        self.api._CurrentChangesetId = 4444

        result = self.api.ChangesetUpdate(
            {
                'test': 'foobar',
                'created_by': 'MyTestOSMApp'
            }
        )

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], '/api/0.6/changeset/4444')
        self.assertTrue(args[2])
        self.assertEquals(
            args[3],
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<osm version="0.6" generator="osmapi/0.2.25">\n'
                '  <changeset visible="true">\n'
                '    <tag k="test" v="foobar"/>\n'
                '    <tag k="created_by" v="MyTestOSMApp"/>\n'
                '  </changeset>\n'
                '</osm>\n'
            )
        )
        self.assertEquals(result, 4444)

    def test_ChangesetUpdate_wo_changeset(self):
        self._http_mock()

        with self.assertRaisesRegexp(
                Exception,
                'No changeset currently opened'):
            self.api.ChangesetUpdate(
                {
                    'test': 'foobar'
                }
            )

    def test_ChangesetCreate(self):
        self._http_mock()

        result = self.api.ChangesetCreate(
            {
                'foobar': 'A new test changeset'
            }
        )

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], '/api/0.6/changeset/create')
        self.assertTrue(args[2])
        self.assertEquals(
            args[3],
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<osm version="0.6" generator="osmapi/0.2.25">\n'
                '  <changeset visible="true">\n'
                '    <tag k="foobar" v="A new test changeset"/>\n'
                '    <tag k="created_by" v="osmapi/0.2.25"/>\n'
                '  </changeset>\n'
                '</osm>\n'
            )
        )
        self.assertEquals(result, 4321)

    def test_ChangesetCreate_with_created_by(self):
        self._http_mock()

        result = self.api.ChangesetCreate(
            {
                'foobar': 'A new test changeset',
                'created_by': 'CoolTestApp',
            }
        )

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], '/api/0.6/changeset/create')
        self.assertTrue(args[2])
        self.assertEquals(
            args[3],
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<osm version="0.6" generator="osmapi/0.2.25">\n'
                '  <changeset visible="true">\n'
                '    <tag k="foobar" v="A new test changeset"/>\n'
                '    <tag k="created_by" v="CoolTestApp"/>\n'
                '  </changeset>\n'
                '</osm>\n'
            )
        )
        self.assertEquals(result, 1234)

    def test_ChangesetCreate_with_open_changeset(self):
        self._http_mock()

        self.api.ChangesetCreate(
            {
                'test': 'an already open changeset',
            }
        )

        with self.assertRaisesRegexp(
                Exception,
                'Changeset already opened'):
            self.api.ChangesetCreate(
                {
                    'test': 'foobar'
                }
            )

    def test_ChangesetClose(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=4444
        )
        self.api._CurrentChangesetId = 4444

        self.api.ChangesetClose()

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'PUT')
        self.assertEquals(args[1], '/api/0.6/changeset/4444/close')
        self.assertTrue(args[2])

    def test_ChangesetClose_with_no_changeset(self):
        self._http_mock()

        with self.assertRaisesRegexp(
                Exception,
                'No changeset currently opened'):
            self.api.ChangesetClose()

    def test_ChangesetUpload_create_node(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=4444
        )
        self.api._CurrentChangesetId = 4444

        changesdata = [
            {
                'type': 'node',
                'action': 'create',
                'data': {
                    'lat': 47.123,
                    'lon': 8.555,
                    'tag': {
                        'amenity': 'place_of_worship',
                        'religion': 'pastafarian'
                    }
                }
            }
        ]

        result = self.api.ChangesetUpload(changesdata)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'POST')
        self.assertEquals(args[1], '/api/0.6/changeset/4444/upload')
        self.assertTrue(args[2])
        self.assertEquals(
            args[3],
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<osmChange version="0.6" generator="osmapi/0.2.25">\n'
                '<create>\n'
                '  <node lat="47.123" lon="8.555" visible="true" '
                'changeset="4444">\n'
                '    <tag k="religion" v="pastafarian"/>\n'
                '    <tag k="amenity" v="place_of_worship"/>\n'
                '  </node>\n'
                '</create>\n'
                '</osmChange>'
            )
        )

        self.assertEquals(result[0]['type'], changesdata[0]['type'])
        self.assertEquals(result[0]['action'], changesdata[0]['action'])

        data = result[0]['data']
        self.assertEquals(data['lat'], changesdata[0]['data']['lat'])
        self.assertEquals(data['lon'], changesdata[0]['data']['lon'])
        self.assertEquals(data['tag'], changesdata[0]['data']['tag'])
        self.assertEquals(data['id'], 4295832900)
        self.assertEquals(result[0]['data']['version'], 1)

    def test_ChangesetUpload_modify_way(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=4444
        )
        self.api._CurrentChangesetId = 4444

        changesdata = [
            {
                'type': 'way',
                'action': 'modify',
                'data': {
                    'id': 4294967296,
                    'version': 2,
                    'nd': [
                        4295832773,
                        4295832773,
                        4294967304,
                        4294967303,
                        4294967300,
                        4608751,
                        4294967305,
                        4294967302,
                        8548430,
                        4294967296,
                        4294967301,
                        4294967298,
                        4294967306,
                        7855737,
                        4294967297,
                        4294967299
                    ],
                    'tag': {
                        'highway': 'secondary',
                        'name': 'Stansted Road'
                    }
                }
            }
        ]

        result = self.api.ChangesetUpload(changesdata)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'POST')
        self.assertEquals(args[1], '/api/0.6/changeset/4444/upload')
        self.assertTrue(args[2])
        self.assertEquals(
            args[3],
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<osmChange version="0.6" generator="osmapi/0.2.25">\n'
                '<modify>\n'
                '  <way id="4294967296" version="2" visible="true" '
                'changeset="4444">\n'
                '    <tag k="name" v="Stansted Road"/>\n'
                '    <tag k="highway" v="secondary"/>\n'
                '    <nd ref="4295832773"/>\n'
                '    <nd ref="4295832773"/>\n'
                '    <nd ref="4294967304"/>\n'
                '    <nd ref="4294967303"/>\n'
                '    <nd ref="4294967300"/>\n'
                '    <nd ref="4608751"/>\n'
                '    <nd ref="4294967305"/>\n'
                '    <nd ref="4294967302"/>\n'
                '    <nd ref="8548430"/>\n'
                '    <nd ref="4294967296"/>\n'
                '    <nd ref="4294967301"/>\n'
                '    <nd ref="4294967298"/>\n'
                '    <nd ref="4294967306"/>\n'
                '    <nd ref="7855737"/>\n'
                '    <nd ref="4294967297"/>\n'
                '    <nd ref="4294967299"/>\n'
                '  </way>\n'
                '</modify>\n'
                '</osmChange>'
            )
        )

        self.assertEquals(result[0]['type'], changesdata[0]['type'])
        self.assertEquals(result[0]['action'], changesdata[0]['action'])

        data = result[0]['data']
        self.assertEquals(data['nd'], changesdata[0]['data']['nd'])
        self.assertEquals(data['tag'], changesdata[0]['data']['tag'])
        self.assertEquals(data['id'], 4294967296)
        self.assertEquals(data['version'], 3)

    def test_ChangesetUpload_delete_relation(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=4444
        )
        self.api._CurrentChangesetId = 4444

        changesdata = [
            {
                'type': 'relation',
                'action': 'delete',
                'data': {
                    'id': 676,
                    'version': 2,
                    'member': [
                        {
                            'ref': 4799,
                            'role': 'outer',
                            'type': 'way'
                        },
                        {
                            'ref': 9391,
                            'role': 'outer',
                            'type': 'way'
                        },
                    ],
                    'tag': {
                        'admin_level': '9',
                        'boundary': 'administrative',
                        'type': 'multipolygon'
                    }
                }
            }
        ]

        result = self.api.ChangesetUpload(changesdata)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'POST')
        self.assertEquals(args[1], '/api/0.6/changeset/4444/upload')
        self.assertTrue(args[2])
        self.assertEquals(
            args[3],
            (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<osmChange version="0.6" generator="osmapi/0.2.25">\n'
                '<delete>\n'
                '  <relation id="676" version="2" visible="true" '
                'changeset="4444">\n'
                '    <tag k="admin_level" v="9"/>\n'
                '    <tag k="boundary" v="administrative"/>\n'
                '    <tag k="type" v="multipolygon"/>\n'
                '    <member type="way" ref="4799" role="outer"/>\n'
                '    <member type="way" ref="9391" role="outer"/>\n'
                '  </relation>\n'
                '</delete>\n'
                '</osmChange>'
            )
        )

        self.assertEquals(result[0]['type'], changesdata[0]['type'])
        self.assertEquals(result[0]['action'], changesdata[0]['action'])

        data = result[0]['data']
        self.assertEquals(data['member'], changesdata[0]['data']['member'])
        self.assertEquals(data['tag'], changesdata[0]['data']['tag'])
        self.assertEquals(data['id'], 676)
        self.assertNotIn('version', data)

    def test_ChangesetDownload(self):
        self._http_mock()

        result = self.api.ChangesetDownload(23123)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/changeset/23123/download')
        self.assertFalse(args[2])

        self.assertEquals(len(result), 16)
        self.assertEquals(
            result[1],
            {
                'action': 'create',
                'type': 'node',
                'data': {
                    'changeset': 23123,
                    'id': 4295668171,
                    'lat': 46.4909781,
                    'lon': 11.2743295,
                    'tag': {
                        'highway': 'traffic_signals'
                    },
                    'timestamp': '2013-05-14T10:33:04Z',
                    'uid': 1178,
                    'user': 'tyrTester06',
                    'version': 1,
                    'visible': True
                }
            }
        )

    def test_ChangesetsGet(self):
        self._http_mock()

        result = self.api.ChangesetsGet(
            only_closed=True,
            username='metaodi'
        )

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(
            args[1],
            '/api/0.6/changesets?display_name=metaodi&closed=1'
        )
        self.assertFalse(args[2])

        self.assertEquals(len(result), 10)

        self.assertEquals(result[41417], {
            'closed_at': '2014-04-29T20:25:01Z',
            'created_at': '2014-04-29T20:25:01Z',
            'id': 41417,
            'max_lat': '58.8997467',
            'max_lon': '22.7364427',
            'min_lat': '58.8501594',
            'min_lon': '22.6984333',
            'open': False,
            'tag': {
                'comment': 'Test delete of relation',
                'created_by': 'iD 1.3.9',
                'imagery_used': 'Bing'
            },
            'uid': 1841,
            'user': 'metaodi'
        })
