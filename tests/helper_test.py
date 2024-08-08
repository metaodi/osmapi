from . import osmapi_test
import osmapi
from unittest import mock
import os

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class TestOsmApiHelper(osmapi_test.TestOsmApi):
    def setUp(self):
        super().setUp()
        self.setupMock()

    def setupMock(self, status=200):
        mock_response = mock.Mock()
        mock_response.status_code = status
        mock_response.reason = "test reason"
        mock_response.content = "test response"

        self.mock_session = mock.Mock()
        self.mock_session.request = mock.Mock(return_value=mock_response)
        self.mock_session.close = mock.Mock()
        self.mock_session.auth = ("testuser", "testpassword")

        self.api = osmapi.OsmApi(
            api=self.api_base,
            session=self.mock_session,
            username="testuser",
            password="testpassword",
        )

    def test_passwordfile_only(self):
        path = os.path.join(__location__, "fixtures", "passwordfile.txt")
        my_api = osmapi.OsmApi(passwordfile=path)
        self.assertEqual("testosm", my_api._username)
        self.assertEqual("testpass", my_api._password)

    def test_passwordfile_with_user(self):
        path = os.path.join(__location__, "fixtures", "passwordfile.txt")
        my_api = osmapi.OsmApi(username="testuser", passwordfile=path)
        self.assertEqual("testuser", my_api._username)
        self.assertEqual("testuserpass", my_api._password)

    def test_passwordfile_with_colon(self):
        path = os.path.join(__location__, "fixtures", "passwordfile_colon.txt")
        my_api = osmapi.OsmApi(username="testuser", passwordfile=path)
        self.assertEqual("testuser", my_api._username)
        self.assertEqual("test:userpass", my_api._password)

    def test_close_call(self):
        self.api.close()
        self.assertEqual(self.api._session._session.close.call_count, 1)

    def test_close_context_manager(self):
        with osmapi.OsmApi() as my_api:
            my_api._session.close = mock.Mock()
        self.assertEqual(my_api._session.close.call_count, 1)

    def test_http_request_get(self):
        response = self.api._session._http_request("GET", "/api/0.6/test", False, None)
        self.mock_session.request.assert_called_with(
            "GET", self.api_base + "/api/0.6/test", data=None, timeout=30
        )
        self.assertEqual(response, "test response")
        self.assertEqual(self.mock_session.request.call_count, 1)

    def test_http_request_put(self):
        data = "data"
        response = self.api._session._http_request(
            "PUT", "/api/0.6/testput", False, data
        )
        self.mock_session.request.assert_called_with(
            "PUT", self.api_base + "/api/0.6/testput", data="data", timeout=30
        )
        self.assertEqual(response, "test response")

    def test_http_request_delete(self):
        data = "delete data"
        response = self.api._session._http_request(
            "PUT", "/api/0.6/testdelete", False, data
        )
        self.mock_session.request.assert_called_with(
            "PUT", self.api_base + "/api/0.6/testdelete", data="delete data", timeout=30
        )
        self.assertEqual(response, "test response")

    def test_http_request_auth(self):
        response = self.api._session._http_request(
            "PUT", "/api/0.6/testauth", True, None
        )
        self.mock_session.request.assert_called_with(
            "PUT", self.api_base + "/api/0.6/testauth", data=None, timeout=30
        )
        self.assertEqual(self.mock_session.auth, ("testuser", "testpassword"))
        self.assertEqual(response, "test response")

    def test_http_request_410_response(self):
        self.setupMock(410)
        with self.assertRaises(osmapi.ElementDeletedApiError) as cm:
            self.api._session._http_request("GET", "/api/0.6/test410", False, None)
        self.assertEqual(cm.exception.status, 410)
        self.assertEqual(cm.exception.reason, "test reason")
        self.assertEqual(cm.exception.payload, "test response")

    def test_http_request_500_response(self):
        self.setupMock(500)
        with self.assertRaises(osmapi.ApiError) as cm:
            self.api._session._http_request(
                "GET", self.api_base + "/api/0.6/test500", False, None
            )
        self.assertEqual(cm.exception.status, 500)
        self.assertEqual(cm.exception.reason, "test reason")
        self.assertEqual(cm.exception.payload, "test response")
