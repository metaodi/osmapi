from __future__ import (unicode_literals, absolute_import)
from . import osmapi_test
from datetime import datetime
import osmapi

try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse


class TestOsmApiNotes(osmapi_test.TestOsmApi):
    def test_NotesGet(self):
        self._session_mock()

        result = self.api.NotesGet(
            -1.4998534,
            45.9667901,
            -1.4831815,
            52.4710193
        )

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        urlParts = urlparse.urlparse(args[1])
        params = urlparse.parse_qs(urlParts.query)
        self.assertEqual(
            params['bbox'][0],
            '-1.499853,45.966790,-1.483181,52.471019'
        )
        self.assertEqual(params['limit'][0], '100')
        self.assertEqual(params['closed'][0], '7')

        self.assertEqual(len(result), 14)
        self.assertEqual(result[2], {
            'id': '231775',
            'lon': -1.4929605,
            'lat': 52.4107312,
            'date_created': datetime(2014, 8, 28, 19, 25, 37),
            'date_closed': datetime(2014, 9, 27, 9, 21, 41),
            'status': 'closed',
            'comments': [
                {
                    'date': datetime(2014, 8, 28, 19, 25, 37),
                    'action': 'opened',
                    'text': "Is it Paynes or Payne's",
                    'html': "<p>Is it Paynes or Payne's</p>",
                    'uid': '1486336',
                    'user': 'Wyken Seagrave'
                },
                {
                    'date': datetime(2014, 9, 26, 13, 5, 33),
                    'action': 'commented',
                    'text': "Royal Mail's postcode finder has PAYNES LANE",
                    'html':
                    (
                        "<p>Royal Mail's postcode finder "
                        "has PAYNES LANE</p>"
                    ),
                    'uid': None,
                    'user': None
                }
            ]
        })

    def test_NoteGet(self):
        self._session_mock()

        result = self.api.NoteGet(1111)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        self.assertEqual(args[1], self.api_base + '/api/0.6/notes/1111')

        self.assertEqual(result, {
            'id': '1111',
            'lon': 12.3133135,
            'lat': 37.9305489,
            'date_created': datetime(2013, 5, 1, 20, 58, 21),
            'date_closed': datetime(2013, 8, 21, 16, 43, 26),
            'status': 'closed',
            'comments': [
                {
                    'date': datetime(2013, 5, 1, 20, 58, 21),
                    'action': 'opened',
                    'text': "It does not exist this path",
                    'html': "<p>It does not exist this path</p>",
                    'uid': '1363438',
                    'user': 'giuseppemari'
                },
                {
                    'date': datetime(2013, 8, 21, 16, 43, 26),
                    'action': 'closed',
                    'text': "there is no path signed",
                    'html': "<p>there is no path signed</p>",
                    'uid': '1714220',
                    'user': 'luschi'
                }
            ]
        })

    def test_NoteGet_invalid_xml(self):
        self._session_mock()

        with self.assertRaises(osmapi.XmlResponseInvalidError):
            self.api.NoteGet(1111)

    def test_NoteCreate(self):
        self._session_mock(auth=True)

        note = {
            'lat': 47.123,
            'lon': 8.432,
            'text': 'This is a test'
        }
        result = self.api.NoteCreate(note)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        urlParts = urlparse.urlparse(args[1])
        params = urlparse.parse_qs(urlParts.query)
        self.assertEqual(params['lat'][0], '47.123')
        self.assertEqual(params['lon'][0], '8.432')
        self.assertEqual(params['text'][0], 'This is a test')

        self.assertEqual(result, {
            'id': '816',
            'lat': 47.123,
            'lon': 8.432,
            'date_created': datetime(2014, 10, 3, 15, 21, 21),
            'date_closed': None,
            'status': 'open',
            'comments': [
                {
                    'date': datetime(2014, 10, 3, 15, 21, 22),
                    'action': 'opened',
                    'text': "This is a test",
                    'html': "<p>This is a test</p>",
                    'uid': '1841',
                    'user': 'metaodi'
                }
            ]
        })

    def test_NoteCreateAnonymous(self):
        self._session_mock()

        note = {
            'lat': 47.123,
            'lon': 8.432,
            'text': 'test 123'
        }
        result = self.api.NoteCreate(note)

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        urlParts = urlparse.urlparse(args[1])
        params = urlparse.parse_qs(urlParts.query)
        self.assertEqual(params['lat'][0], '47.123')
        self.assertEqual(params['lon'][0], '8.432')
        self.assertEqual(params['text'][0], 'test 123')

        self.assertEqual(result, {
            'id': '842',
            'lat': 58.3368222,
            'lon': 25.8826183,
            'date_created': datetime(2015, 1, 3, 10, 49, 39),
            'date_closed': None,
            'status': 'open',
            'comments': [
                {
                    'date': datetime(2015, 1, 3, 10, 49, 39),
                    'action': 'opened',
                    'text': "test 123",
                    'html': "<p>test 123</p>",
                    'uid': None,
                    'user': None,
                }
            ]
        })

    def test_NoteComment(self):
        self._session_mock(auth=True)

        result = self.api.NoteComment(812, 'This is a comment')

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            self.api_base + '/api/0.6/notes/812/comment?text=This+is+a+comment'
        )

        self.assertEqual(result, {
            'id': '812',
            'lat': 47.123,
            'lon': 8.432,
            'date_created': datetime(2014, 10, 3, 15, 11, 5),
            'date_closed': None,
            'status': 'open',
            'comments': [
                {
                    'date': datetime(2014, 10, 3, 15, 11, 5),
                    'action': 'opened',
                    'text': "This is a test",
                    'html': "<p>This is a test</p>",
                    'uid': '1841',
                    'user': 'metaodi'
                },
                {
                    'date': datetime(2014, 10, 4, 22, 36, 35),
                    'action': 'commented',
                    'text': "This is a comment",
                    'html': "<p>This is a comment</p>",
                    'uid': '1841',
                    'user': 'metaodi'
                }
            ]
        })

    def test_NoteCommentAnonymous(self):
        self._session_mock()

        result = self.api.NoteComment(842, 'blubb')

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            self.api_base + '/api/0.6/notes/842/comment?text=blubb'
        )

        self.assertEqual(result, {
            'id': '842',
            'lat': 58.3368222,
            'lon': 25.8826183,
            'date_created': datetime(2015, 1, 3, 10, 49, 39),
            'date_closed': None,
            'status': 'open',
            'comments': [
                {
                    'date': datetime(2015, 1, 3, 10, 49, 39),
                    'action': 'opened',
                    'text': "test 123",
                    'html': "<p>test 123</p>",
                    'uid': None,
                    'user': None,
                },
                {
                    'date': datetime(2015, 1, 3, 11, 6, 0),
                    'action': 'commented',
                    'text': "blubb",
                    'html': "<p>blubb</p>",
                    'uid': None,
                    'user': None,
                }
            ]
        })

    def test_NoteClose(self):
        self._session_mock(auth=True)

        result = self.api.NoteClose(814, 'Close this note!')

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            self.api_base + '/api/0.6/notes/814/close?text=Close+this+note%21'
        )

        self.assertEqual(result, {
            'id': '815',
            'lat': 47.123,
            'lon': 8.432,
            'date_created': datetime(2014, 10, 3, 15, 20, 57),
            'date_closed': datetime(2014, 10, 5, 16, 35, 13),
            'status': 'closed',
            'comments': [
                {
                    'date': datetime(2014, 10, 3, 15, 20, 57),
                    'action': 'opened',
                    'text': "This is a test",
                    'html': "<p>This is a test</p>",
                    'uid': '1841',
                    'user': 'metaodi'
                },
                {
                    'date': datetime(2014, 10, 5, 16, 35, 13),
                    'action': 'closed',
                    'text': "Close this note!",
                    'html': "<p>Close this note!</p>",
                    'uid': '1841',
                    'user': 'metaodi'
                }
            ]
        })

    def test_NoteReopen(self):
        self._session_mock(auth=True)

        result = self.api.NoteReopen(815, 'Reopen this note!')

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'POST')
        self.assertEqual(
            args[1],
            (self.api_base +
             '/api/0.6/notes/815/reopen?text=Reopen+this+note%21')
        )

        self.assertEqual(result, {
            'id': '815',
            'lat': 47.123,
            'lon': 8.432,
            'date_created': datetime(2014, 10, 3, 15, 20, 57),
            'date_closed': None,
            'status': 'open',
            'comments': [
                {
                    'date': datetime(2014, 10, 3, 15, 20, 57),
                    'action': 'opened',
                    'text': "This is a test",
                    'html': "<p>This is a test</p>",
                    'uid': '1841',
                    'user': 'metaodi'
                },
                {
                    'date': datetime(2014, 10, 5, 16, 35, 13),
                    'action': 'closed',
                    'text': "Close this note!",
                    'html': "<p>Close this note!</p>",
                    'uid': '1841',
                    'user': 'metaodi'
                },
                {
                    'date': datetime(2014, 10, 5, 16, 44, 56),
                    'action': 'reopened',
                    'text': "Reopen this note!",
                    'html': "<p>Reopen this note!</p>",
                    'uid': '1841',
                    'user': 'metaodi'
                }
            ]
        })

    def test_NotesSearch(self):
        self._session_mock()

        result = self.api.NotesSearch('street')

        args, kwargs = self.api._session.request.call_args
        self.assertEqual(args[0], 'GET')
        urlParts = urlparse.urlparse(args[1])
        params = urlparse.parse_qs(urlParts.query)
        self.assertEqual(params['q'][0], 'street')
        self.assertEqual(params['limit'][0], '100')
        self.assertEqual(params['closed'][0], '7')

        self.assertEqual(len(result), 3)
        self.assertEqual(result[1], {
            'id': '788',
            'lon': 11.96395,
            'lat': 57.70301,
            'date_created': datetime(2014, 7, 16, 16, 12, 41),
            'date_closed': None,
            'status': 'open',
            'comments': [
                {
                    'date': datetime(2014, 7, 16, 16, 12, 41),
                    'action': 'opened',
                    'text': "One way street:\ncomment",
                    'html': "<p>One way street:\n<br />comment</p>",
                    'uid': None,
                    'user': None
                }
            ]
        })
