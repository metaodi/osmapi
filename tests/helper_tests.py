from __future__ import (unicode_literals, absolute_import)
from nose.tools import *  # noqa
from . import osmapi_tests
import osmapi
import mock
import os

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


class TestOsmApiHelper(osmapi_tests.TestOsmApi):
    def setUp(self):
        super(TestOsmApiHelper, self).setUp()
        self.setupMock()

    def setupMock(self, status=200):
        mock_response = mock.Mock()
        mock_response.status = status
        mock_response.reason = "test reason"
        mock_response.read = mock.Mock(return_value='test response')
        self.api._conn.getresponse = mock.Mock(return_value=mock_response)
        self.api._conn.putrequest = mock.Mock()
        self.api._conn.putheader = mock.Mock()
        self.api._conn.send = mock.Mock()
        self.api._conn.endheaders = mock.Mock()
        self.api._username = 'testuser'
        self.api._password = 'testpassword'

    def test_passwordfile(self):
        path = os.path.join(
            __location__,
            'fixtures',
            'passwordfile.txt'
        )
        my_api = osmapi.OsmApi(passwordfile=path)
        self.assertEquals('testosm', my_api._username)
        self.assertEquals('testpass', my_api._password)

    def test_http_request_get(self):
        response = self.api._http_request(
            'GET',
            '/api/0.6/test',
            False,
            None
        )
        self.api._conn.putrequest.assert_called_with('GET', '/api/0.6/test')
        self.assertEquals(response, "test response")
        self.assertEquals(self.api._conn.putheader.call_count, 1)

    def test_http_request_put(self):
        response = self.api._http_request(
            'PUT',
            '/api/0.6/testput',
            False,
            "data"
        )
        self.api._conn.putrequest.assert_called_with(
            'PUT',
            '/api/0.6/testput'
        )
        self.assertEquals(response, "test response")
        self.assertEquals(self.api._conn.putheader.call_count, 2)
        args = self.api._conn.putheader.call_args_list[1]
        header, value = args[0]
        self.assertEquals(header, 'Content-Length')
        self.assertEquals(value, 4)

    def test_http_request_delete(self):
        response = self.api._http_request(
            'PUT',
            '/api/0.6/testdelete',
            False,
            "delete data"
        )
        self.api._conn.putrequest.assert_called_with(
            'PUT',
            '/api/0.6/testdelete'
        )
        self.assertEquals(response, "test response")
        self.assertEquals(self.api._conn.putheader.call_count, 2)
        args = self.api._conn.putheader.call_args_list[1]
        header, value = args[0]
        self.assertEquals(header, 'Content-Length')
        self.assertEquals(value, 11)

    def test_http_request_auth(self):
        response = self.api._http_request(
            'PUT',
            '/api/0.6/testauth',
            True,
            None
        )
        self.api._conn.putrequest.assert_called_with(
            'PUT',
            '/api/0.6/testauth'
        )
        self.assertEquals(response, "test response")

        self.assertEquals(self.api._conn.putheader.call_count, 2)
        args = self.api._conn.putheader.call_args_list[1]
        header, value = args[0]
        self.assertEquals(header, 'Authorization')
        self.assertEquals(value, 'Basic dGVzdHVzZXI6dGVzdHBhc3N3b3Jk')

    def test_http_request_410_response(self):
        self.setupMock(410)
        response = self.api._http_request(
            'GET',
            '/api/0.6/test410',
            False,
            None
        )
        self.api._conn.putrequest.assert_called_with(
            'GET',
            '/api/0.6/test410'
        )
        self.assertIsNone(response, "test response")

    def test_http_request_500_response(self):
        self.setupMock(500)
        with self.assertRaises(osmapi.ApiError) as cm:
            self.api._http_request(
                'GET',
                '/api/0.6/test500',
                False,
                None
            )
        self.assertEquals(cm.exception.status, 500)
        self.assertEquals(cm.exception.reason, "test reason")
        self.assertEquals(cm.exception.payload, "test response")
