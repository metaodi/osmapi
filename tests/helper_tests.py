from __future__ import (unicode_literals, absolute_import)
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
        mock_response.content = 'test response'
        self.api._session.request = mock.Mock(return_value=mock_response)
        self.api._session.close = mock.Mock()
        self.api._username = 'testuser'
        self.api._password = 'testpassword'

    def test_passwordfile_only(self):
        path = os.path.join(
            __location__,
            'fixtures',
            'passwordfile.txt'
        )
        my_api = osmapi.OsmApi(passwordfile=path)
        self.assertEquals('testosm', my_api._username)
        self.assertEquals('testpass', my_api._password)

    def test_passwordfile_with_user(self):
        path = os.path.join(
            __location__,
            'fixtures',
            'passwordfile.txt'
        )
        my_api = osmapi.OsmApi(username='testuser', passwordfile=path)
        self.assertEquals('testuser', my_api._username)
        self.assertEquals('testuserpass', my_api._password)

    def test_passwordfile_with_colon(self):
        path = os.path.join(
            __location__,
            'fixtures',
            'passwordfile_colon.txt'
        )
        my_api = osmapi.OsmApi(username='testuser', passwordfile=path)
        self.assertEquals('testuser', my_api._username)
        self.assertEquals('test:userpass', my_api._password)

    def test_close_call(self):
        self.api.close()
        self.assertEquals(self.api._session.close.call_count, 1)

    def test_close_context_manager(self):
        with osmapi.OsmApi() as my_api:
            my_api._session.close = mock.Mock()
        self.assertEquals(my_api._session.close.call_count, 1)

    def test_http_request_get(self):
        response = self.api._http_request(
            'GET',
            '/api/0.6/test',
            False,
            None
        )
        self.api._session.request.assert_called_with(
            'GET',
            self.api_base + '/api/0.6/test',
            auth=None,
            data=None
        )
        self.assertEquals(response, "test response")
        self.assertEquals(self.api._session.request.call_count, 1)

    def test_http_request_put(self):
        data = "data"
        response = self.api._http_request(
            'PUT',
            '/api/0.6/testput',
            False,
            data
        )
        self.api._session.request.assert_called_with(
            'PUT',
            self.api_base + '/api/0.6/testput',
            data="data",
            auth=None
        )
        self.assertEquals(response, "test response")

    def test_http_request_delete(self):
        data = "delete data"
        response = self.api._http_request(
            'PUT',
            '/api/0.6/testdelete',
            False,
            data
        )
        self.api._session.request.assert_called_with(
            'PUT',
            self.api_base + '/api/0.6/testdelete',
            data="delete data",
            auth=None
        )
        self.assertEquals(response, "test response")

    def test_http_request_auth(self):
        response = self.api._http_request(
            'PUT',
            '/api/0.6/testauth',
            True,
            None
        )
        self.api._session.request.assert_called_with(
            'PUT',
            self.api_base + '/api/0.6/testauth',
            auth=('testuser', 'testpassword'),
            data=None
        )
        self.assertEquals(response, "test response")

    def test_http_request_410_response(self):
        self.setupMock(410)
        with self.assertRaises(osmapi.ElementDeletedApiError) as cm:
            self.api._http_request(
                'GET',
                '/api/0.6/test410',
                False,
                None
            )
        self.assertEquals(cm.exception.status, 410)
        self.assertEquals(cm.exception.reason, "test reason")
        self.assertEquals(cm.exception.payload, "test response")

    def test_http_request_500_response(self):
        self.setupMock(500)
        with self.assertRaises(osmapi.ApiError) as cm:
            self.api._http_request(
                'GET',
                self.api_base + '/api/0.6/test500',
                False,
                None
            )
        self.assertEquals(cm.exception.status, 500)
        self.assertEquals(cm.exception.reason, "test reason")
        self.assertEquals(cm.exception.payload, "test response")
