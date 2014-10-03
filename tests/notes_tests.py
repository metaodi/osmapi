from __future__ import (unicode_literals, absolute_import)
from nose.tools import *  # noqa
from . import osmapi_tests


class TestOsmApiNotes(osmapi_tests.TestOsmApi):
    def test_NotesGet(self):
        self._http_mock()

        result = self.api.NotesGet(
            -1.4998534,
            45.9667901,
            -1.4831815,
            52.4710193
        )

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(
            args[1],
            (
                '/api/0.6/notes?bbox=-1.499853,45.966790,-1.483181,52.471019'
                '&limit=100&closed=7'
            )
        )

        self.assertEquals(len(result), 14)
        self.assertEquals(result['231775'], {
            'id': '231775',
            'lon': -1.4929605,
            'lat': 52.4107312,
            'date_created': '2014-08-28 19:25:37 UTC',
            'date_closed': '2014-09-27 09:21:41 UTC',
            'status': 'closed',
            'comments': [
                {
                    'date': '2014-08-28 19:25:37 UTC',
                    'action': 'opened',
                    'text': "Is it Paynes or Payne's",
                    'html': "<p>Is it Paynes or Payne's</p>",
                    'uid': '1486336',
                    'user': 'Wyken Seagrave'
                },
                {
                    'date': '2014-09-26 13:05:33 UTC',
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
        self._http_mock()

        result = self.api.NoteGet(1111)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'GET')
        self.assertEquals(args[1], '/api/0.6/notes/1111')

        self.assertEquals(result, {
            'id': '1111',
            'lon': 12.3133135,
            'lat': 37.9305489,
            'date_created': '2013-05-01 20:58:21 UTC',
            'date_closed': '2013-08-21 16:43:26 UTC',
            'status': 'closed',
            'comments': [
                {
                    'date': '2013-05-01 20:58:21 UTC',
                    'action': 'opened',
                    'text': "It does not exist this path",
                    'html': "<p>It does not exist this path</p>",
                    'uid': '1363438',
                    'user': 'giuseppemari'
                },
                {
                    'date': '2013-08-21 16:43:26 UTC',
                    'action': 'closed',
                    'text': "there is no path signed",
                    'html': "<p>there is no path signed</p>",
                    'uid': '1714220',
                    'user': 'luschi'
                }
            ]
        })

    def test_NoteCreate(self):
        self._http_mock()

        note = {
            'lat': 47.123,
            'lon': 8.432,
            'text': 'This is a test'
        }
        result = self.api.NoteCreate(note)

        args, kwargs = self.api._http_request.call_args
        self.assertEquals(args[0], 'POST')
        self.assertEquals(
            args[1],
            '/api/0.6/notes?lat=47.123&text=This+is+a+test&lon=8.432'
        )

        self.assertEquals(result, {
            'id': '816',
            'lat': 47.123,
            'lon': 8.432,
            'date_created': '2014-10-03 15:21:21 UTC',
            'date_closed': None,
            'status': 'open',
            'comments': [
                {
                    'date': '2014-10-03 15:21:22 UTC',
                    'action': 'opened',
                    'text': "This is a test",
                    'html': "<p>This is a test</p>",
                    'uid': '1841',
                    'user': 'metaodi'
                }
            ]
        })
