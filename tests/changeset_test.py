from __future__ import (unicode_literals, absolute_import)
from . import osmapi_test
import osmapi
import mock
import xmltodict
import datetime
try:
    import urlparse
except Exception:
    import urllib
    urlparse = urllib.parse


def recursive_sort(col):  # noqa
    """
    Function to recursive sort a collection
    that might contain lists, dicts etc.
    In Python 3.x a list of dicts is sorted by it's hash
    """
    if hasattr(col, '__iter__'):
        if isinstance(col, list):
            try:
                col = sorted(col)
            except TypeError:  # in Python 3.x: lists of dicts are not sortable
                col = sorted(col, key=lambda k: hash(frozenset(k.items())))
            except Exception:
                pass

            for idx, elem in enumerate(col):
                col[idx] = recursive_sort(elem)
        elif isinstance(col, dict):
            for elem in col:
                try:
                    col[elem] = recursive_sort(col[elem])
                except IndexError:
                    pass
    return col


def xmltosorteddict(xml):
    xml_dict = xmltodict.parse(xml, dict_constructor=dict)
    return recursive_sort(xml_dict)


class TestOsmApiChangeset(osmapi_test.TestOsmApi):
    def test_ChangesetGet(self):
        self._session_mock()

        result = self.api.ChangesetGet(123)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], self.api_base + '/api/0.6/changeset/123')

        self.assertEqual(result, {
            'id': 123,
            'closed_at': datetime.datetime(2009, 9, 7, 22, 57, 37),
            'created_at': datetime.datetime(2009, 9, 7, 21, 57, 36),
            'discussion': [],
            'max_lat': '52.4710193',
            'max_lon': '-1.4831815',
            'min_lat': '45.9667901',
            'min_lon': '-1.4998534',
            'open': False,
            'user': 'randomjunk',
            'uid': 3,
            'tag': {
                'comment': 'correct node bug',
                'created_by': 'Potlatch 1.2a',
            },
        })

    def test_ChangesetUpdate(self):
        self._session_mock(auth=True)

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

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertEqual(args[1], self.api_base + '/api/0.6/changeset/4444')
        self.assertEqual(
            xmltosorteddict(kwargs['data']),
            xmltosorteddict(
                b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<osm version="0.6" generator="osmapi/2.0.2">\n'
                b'  <changeset visible="true">\n'
                b'    <tag k="test" v="foobar"/>\n'
                b'    <tag k="created_by" v="osmapi/2.0.2"/>\n'
                b'  </changeset>\n'
                b'</osm>\n'
            )
        )
        self.assertEqual(result, 4444)

    def test_ChangesetUpdate_with_created_by(self):
        self._session_mock(auth=True)

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

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertEqual(args[1], self.api_base + '/api/0.6/changeset/4444')
        self.assertEqual(
            xmltosorteddict(kwargs['data']),
            xmltosorteddict(
                b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<osm version="0.6" generator="osmapi/2.0.2">\n'
                b'  <changeset visible="true">\n'
                b'    <tag k="test" v="foobar"/>\n'
                b'    <tag k="created_by" v="MyTestOSMApp"/>\n'
                b'  </changeset>\n'
                b'</osm>\n'
            )
        )
        self.assertEqual(result, 4444)

    def test_ChangesetUpdate_wo_changeset(self):
        self._session_mock()

        with self.assertRaisesRegex(
                osmapi.NoChangesetOpenError,
                'No changeset currently opened'):
            self.api.ChangesetUpdate(
                {
                    'test': 'foobar'
                }
            )

    def test_ChangesetCreate(self):
        self._session_mock(auth=True)

        result = self.api.ChangesetCreate(
            {
                'foobar': 'A new test changeset'
            }
        )

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertEqual(args[1], self.api_base + '/api/0.6/changeset/create')
        self.assertEqual(
            xmltosorteddict(kwargs['data']),
            xmltosorteddict(
                b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<osm version="0.6" generator="osmapi/2.0.2">\n'
                b'  <changeset visible="true">\n'
                b'    <tag k="foobar" v="A new test changeset"/>\n'
                b'    <tag k="created_by" v="osmapi/2.0.2"/>\n'
                b'  </changeset>\n'
                b'</osm>\n'
            )
        )
        self.assertEqual(result, 4321)

    def test_ChangesetCreate_with_created_by(self):
        self._session_mock(auth=True)

        result = self.api.ChangesetCreate(
            {
                'foobar': 'A new test changeset',
                'created_by': 'CoolTestApp',
            }
        )

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertEqual(args[1], self.api_base + '/api/0.6/changeset/create')
        self.assertEqual(
            xmltosorteddict(kwargs['data']),
            xmltosorteddict(
                b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<osm version="0.6" generator="osmapi/2.0.2">\n'
                b'  <changeset visible="true">\n'
                b'    <tag k="foobar" v="A new test changeset"/>\n'
                b'    <tag k="created_by" v="CoolTestApp"/>\n'
                b'  </changeset>\n'
                b'</osm>\n'
            )
        )
        self.assertEqual(result, 1234)

    def test_ChangesetCreate_with_open_changeset(self):
        self._session_mock(auth=True)

        self.api.ChangesetCreate(
            {
                'test': 'an already open changeset',
            }
        )

        with self.assertRaisesRegex(
                osmapi.ChangesetAlreadyOpenError,
                'Changeset already opened'):
            self.api.ChangesetCreate(
                {
                    'test': 'foobar'
                }
            )

    def test_ChangesetClose(self):
        self._session_mock(auth=True)

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=4444
        )
        self.api._CurrentChangesetId = 4444

        self.api.ChangesetClose()

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/changeset/4444/close'
        )

    def test_ChangesetClose_with_no_changeset(self):
        self._session_mock()

        with self.assertRaisesRegex(
                osmapi.NoChangesetOpenError,
                'No changeset currently opened'):
            self.api.ChangesetClose()

    def test_ChangesetUpload_create_node(self):
        self._session_mock(auth=True)

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

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/changeset/4444/upload'
        )
        self.assertEqual(
            xmltosorteddict(kwargs['data']),
            xmltosorteddict(
                b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<osmChange version="0.6" generator="osmapi/2.0.2">\n'
                b'<create>\n'
                b'  <node lat="47.123" lon="8.555" visible="true" '
                b'changeset="4444">\n'
                b'    <tag k="religion" v="pastafarian"/>\n'
                b'    <tag k="amenity" v="place_of_worship"/>\n'
                b'  </node>\n'
                b'</create>\n'
                b'</osmChange>'
            )
        )

        self.assertEqual(result[0]['type'], changesdata[0]['type'])
        self.assertEqual(result[0]['action'], changesdata[0]['action'])

        data = result[0]['data']
        self.assertEqual(data['lat'], changesdata[0]['data']['lat'])
        self.assertEqual(data['lon'], changesdata[0]['data']['lon'])
        self.assertEqual(data['tag'], changesdata[0]['data']['tag'])
        self.assertEqual(data['id'], 4295832900)
        self.assertEqual(result[0]['data']['version'], 1)

    def test_ChangesetUpload_modify_way(self):
        self._session_mock(auth=True)

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

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/changeset/4444/upload'
        )
        self.assertEqual(
            xmltosorteddict(kwargs['data']),
            xmltosorteddict(
                b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<osmChange version="0.6" generator="osmapi/2.0.2">\n'
                b'<modify>\n'
                b'  <way id="4294967296" version="2" visible="true" '
                b'changeset="4444">\n'
                b'    <tag k="name" v="Stansted Road"/>\n'
                b'    <tag k="highway" v="secondary"/>\n'
                b'    <nd ref="4295832773"/>\n'
                b'    <nd ref="4295832773"/>\n'
                b'    <nd ref="4294967304"/>\n'
                b'    <nd ref="4294967303"/>\n'
                b'    <nd ref="4294967300"/>\n'
                b'    <nd ref="4608751"/>\n'
                b'    <nd ref="4294967305"/>\n'
                b'    <nd ref="4294967302"/>\n'
                b'    <nd ref="8548430"/>\n'
                b'    <nd ref="4294967296"/>\n'
                b'    <nd ref="4294967301"/>\n'
                b'    <nd ref="4294967298"/>\n'
                b'    <nd ref="4294967306"/>\n'
                b'    <nd ref="7855737"/>\n'
                b'    <nd ref="4294967297"/>\n'
                b'    <nd ref="4294967299"/>\n'
                b'  </way>\n'
                b'</modify>\n'
                b'</osmChange>'
            )
        )

        self.assertEqual(result[0]['type'], changesdata[0]['type'])
        self.assertEqual(result[0]['action'], changesdata[0]['action'])

        data = result[0]['data']
        self.assertEqual(data['nd'], changesdata[0]['data']['nd'])
        self.assertEqual(data['tag'], changesdata[0]['data']['tag'])
        self.assertEqual(data['id'], 4294967296)
        self.assertEqual(data['version'], 3)

    def test_ChangesetUpload_delete_relation(self):
        self._session_mock(auth=True)

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

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/changeset/4444/upload'
        )
        self.assertEqual(
            xmltosorteddict(kwargs['data']),
            xmltosorteddict(
                b'<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<osmChange version="0.6" generator="osmapi/2.0.2">\n'
                b'<delete>\n'
                b'  <relation id="676" version="2" visible="true" '
                b'changeset="4444">\n'
                b'    <tag k="admin_level" v="9"/>\n'
                b'    <tag k="boundary" v="administrative"/>\n'
                b'    <tag k="type" v="multipolygon"/>\n'
                b'    <member type="way" ref="4799" role="outer"/>\n'
                b'    <member type="way" ref="9391" role="outer"/>\n'
                b'  </relation>\n'
                b'</delete>\n'
                b'</osmChange>'
            )
        )

        self.assertEqual(result[0]['type'], changesdata[0]['type'])
        self.assertEqual(result[0]['action'], changesdata[0]['action'])

        data = result[0]['data']
        self.assertEqual(data['member'], changesdata[0]['data']['member'])
        self.assertEqual(data['tag'], changesdata[0]['data']['tag'])
        self.assertEqual(data['id'], 676)
        self.assertNotIn('version', data)

    def test_ChangesetUpload_invalid_response(self):
        self._session_mock(auth=True)

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

        with self.assertRaises(osmapi.XmlResponseInvalidError):
            self.api.ChangesetUpload(changesdata)

    def test_ChangesetDownload(self):
        self._session_mock()

        result = self.api.ChangesetDownload(23123)

        args, _ = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/changeset/23123/download'
        )

        self.assertEqual(len(result), 16)
        self.assertEqual(
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
                    'timestamp': datetime.datetime(2013, 5, 14, 10, 33, 4),
                    'uid': 1178,
                    'user': 'tyrTester06',
                    'version': 1,
                    'visible': True
                }
            }
        )

    def test_ChangesetDownload_invalid_response(self):
        self._session_mock()
        with self.assertRaises(osmapi.XmlResponseInvalidError):
            self.api.ChangesetDownload(23123)

    def test_ChangesetDownloadContainingUnicode(self):
        self._session_mock()

        # This changeset contains unicode tag values
        # Note that the fixture data has been reduced from the
        # original from openstreetmap.org
        result = self.api.ChangesetDownload(37393499)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[1],
            {
                'action': 'create',
                'type': 'way',
                'data': {
                    'changeset': 37393499,
                    'id': 399491497,
                    'nd': [4022271571, 4022271567, 4022271565],
                    'tag': {'highway': 'service',
                            # UTF-8 encoded 'LATIN SMALL LETTER O WITH STROKE'
                            # Aka. 0xf8 in latin-1/ISO 8859-1
                            'name': b'S\xc3\xb8nderskovvej'.decode('utf-8'),
                            'service': 'driveway'},
                    'timestamp': datetime.datetime(2016, 2, 23, 16, 55, 35),
                    'uid': 328556,
                    'user': 'InternationalUser',
                    'version': 1,
                    'visible': True
                }
            }
        )

    def test_ChangesetsGet(self):
        self._session_mock()

        result = self.api.ChangesetsGet(
            only_closed=True,
            username='metaodi'
        )

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            dict(urlparse.parse_qsl(urlparse.urlparse(args[1])[4])),
            {
                'display_name': 'metaodi',
                'closed': '1'
            }
        )

        self.assertEqual(len(result), 10)

        self.assertEqual(result[41417], {
            'closed_at': datetime.datetime(2014, 4, 29, 20, 25, 1),
            'created_at': datetime.datetime(2014, 4, 29, 20, 25, 1),
            'id': 41417,
            'discussion': [],
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

    def test_ChangesetGetWithComment(self):
        self._session_mock()

        result = self.api.ChangesetGet(52924, include_discussion=True)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(
            args[1],
            self.api_base + '/api/0.6/changeset/52924?include_discussion=true'
        )

        self.assertEqual(result, {
            'id': 52924,
            'closed_at': datetime.datetime(2015, 1, 1, 14, 54, 2),
            'created_at': datetime.datetime(2015, 1, 1, 14, 54, 1),
            'comments_count': 3,
            'max_lat': '58.3369242',
            'max_lon': '25.8829107',
            'min_lat': '58.336813',
            'min_lon': '25.8823273',
            'discussion': [
                {
                    'date':  datetime.datetime(2015, 1, 1, 18, 56, 48),
                    'text': 'test',
                    'uid': 1841,
                    'user': 'metaodi',
                },
                {
                    'date':  datetime.datetime(2015, 1, 1, 18, 58, 3),
                    'text': 'another comment',
                    'uid': 1841,
                    'user': 'metaodi',
                },
                {
                    'date':  datetime.datetime(2015, 1, 1, 19, 16, 5),
                    'text': 'hello',
                    'uid': 1841,
                    'user': 'metaodi',
                },
            ],
            'open': False,
            'user': 'metaodi',
            'uid': 1841,
            'tag': {
                'comment': 'My test',
                'created_by': 'osmapi/0.4.1',
            },
        })

    def test_ChangesetComment(self):
        self._session_mock(auth=True)

        result = self.api.ChangesetComment(
            123,
            comment="test comment"
        )

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/changeset/123/comment'
        )
        self.assertEqual(
            kwargs['data'],
            "text=test+comment"
        )
        self.assertEqual(result, {
            'id': 123,
            'closed_at': datetime.datetime(2009, 9, 7, 22, 57, 37),
            'created_at': datetime.datetime(2009, 9, 7, 21, 57, 36),
            'discussion': [],
            'max_lat': '52.4710193',
            'max_lon': '-1.4831815',
            'min_lat': '45.9667901',
            'min_lon': '-1.4998534',
            'open': False,
            'user': 'randomjunk',
            'uid': 3,
            'tag': {
                'comment': 'correct node bug',
                'created_by': 'Potlatch 1.2a',
            },
        })

    def test_ChangesetSubscribe(self):
        self._session_mock(auth=True)

        result = self.api.ChangesetSubscribe(123)

        args, _ = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/changeset/123/subscribe'
        )
        self.assertEqual(result, {
            'id': 123,
            'closed_at': datetime.datetime(2009, 9, 7, 22, 57, 37),
            'created_at': datetime.datetime(2009, 9, 7, 21, 57, 36),
            'discussion': [],
            'max_lat': '52.4710193',
            'max_lon': '-1.4831815',
            'min_lat': '45.9667901',
            'min_lon': '-1.4998534',
            'open': False,
            'user': 'randomjunk',
            'uid': 3,
            'tag': {
                'comment': 'correct node bug',
                'created_by': 'Potlatch 1.2a',
            },
        })

    def test_ChangesetSubscribeWhenAlreadySubscribed(self):
        self._session_mock(auth=True, status=409)

        with self.assertRaises(osmapi.AlreadySubscribedApiError) as cm:
            self.api.ChangesetSubscribe(52924)

        self.assertEqual(cm.exception.status, 409)
        self.assertEqual(
            cm.exception.payload,
            "You are already subscribed to changeset 52924."
        )

    def test_ChangesetUnsubscribe(self):
        self._session_mock(auth=True)

        result = self.api.ChangesetUnsubscribe(123)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            f'{self.api_base}/api/0.6/changeset/123/unsubscribe'
        )
        self.assertEqual(result, {
            'id': 123,
            'closed_at': datetime.datetime(2009, 9, 7, 22, 57, 37),
            'created_at': datetime.datetime(2009, 9, 7, 21, 57, 36),
            'discussion': [],
            'max_lat': '52.4710193',
            'max_lon': '-1.4831815',
            'min_lat': '45.9667901',
            'min_lon': '-1.4998534',
            'open': False,
            'user': 'randomjunk',
            'uid': 3,
            'tag': {
                'comment': 'correct node bug',
                'created_by': 'Potlatch 1.2a',
            },
        })

    def test_ChangesetUnsubscribeWhenNotSubscribed(self):
        self._session_mock(auth=True, status=404)

        with self.assertRaises(osmapi.NotSubscribedApiError) as cm:
            self.api.ChangesetUnsubscribe(52924)

        self.assertEqual(cm.exception.status, 404)
        self.assertEqual(
            cm.exception.payload,
            "You are not subscribed to changeset 52924."
        )
