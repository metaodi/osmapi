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
        mock_response.status_code = status
        mock_response.reason = "test reason"
        mock_response.text = 'test response'
        self.api._conn.get = mock.Mock(return_value=mock_response)
        self.api._conn.put = mock.Mock(return_value=mock_response)
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
            self.api._conn.get,
            '/api/0.6/test',
            False,
            None
        )
        self.api._conn.get.assert_called_with(self.api_base + '/api/0.6/test',
                                              headers={})
        self.assertEquals(response, "test response")
        self.assertEquals(self.api._conn.get.call_count, 1)

    def test_http_request_put(self):
        data = "data"
        response = self.api._http_request(
            self.api._conn.put,
            '/api/0.6/testput',
            False,
            data
        )
        self.api._conn.put.assert_called_with(
            self.api_base + '/api/0.6/testput',
            data="data",
            headers={'Content-Length': len(data)}
        )
        self.assertEquals(response, "test response")

    def test_http_request_delete(self):
        data = "delete data"
        response = self.api._http_request(
            self.api._conn.put,
            '/api/0.6/testdelete',
            False,
            data
        )
        self.api._conn.put.assert_called_with(
            self.api_base + '/api/0.6/testdelete',
            data="delete data",
            headers={'Content-Length': len(data)}
        )
        self.assertEquals(response, "test response")

    def test_http_request_auth(self):
        response = self.api._http_request(
            self.api._conn.put,
            '/api/0.6/testauth',
            True,
            None
        )
        self.api._conn.put.assert_called_with(
            self.api_base + '/api/0.6/testauth',
            headers={'Authorization': 'Basic dGVzdHVzZXI6dGVzdHBhc3N3b3Jk'}
        )
        self.assertEquals(response, "test response")

    def test_http_request_410_response(self):
        self.setupMock(410)
        response = self.api._http_request(
            self.api._conn.get,
            '/api/0.6/test410',
            False,
            None
        )
        self.api._conn.get.assert_called_with(
            self.api_base + '/api/0.6/test410',
            headers={}
        )
        self.assertIsNone(response, "test response")

    def test_http_request_500_response(self):
        self.setupMock(500)
        with self.assertRaises(osmapi.ApiError) as cm:
            self.api._http_request(
                self.api._conn.get,
                self.api_base + '/api/0.6/test500',
                False,
                None
            )
            self.assertEquals(cm.exception.status, 500)
            self.assertEquals(cm.exception.reason, "test reason")
            self.assertEquals(cm.exception.payload, "test response")
