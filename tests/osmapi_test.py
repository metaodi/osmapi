from osmapi import OsmApi
from unittest import mock
import os
import unittest
import codecs

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class TestOsmApi(unittest.TestCase):
    def setUp(self):
        self.api_base = "http://api06.dev.openstreetmap.org"
        self.api = OsmApi(api=self.api_base)
        self.maxDiff = None
        print(self._testMethodName)
        print(self.api)

    def _session_mock(self, auth=False, filenames=None, status=200):
        response_mock = mock.Mock()
        response_mock.status_code = status
        return_values = self._return_values(filenames)
        print(filenames)
        print(return_values)
        assert len(return_values) < 2
        if return_values:
            response_mock.content = return_values[0]

        self.session_mock = mock.Mock()
        self.session_mock.request = mock.Mock(return_value=response_mock)
        self.session_mock.auth = None

        if auth:
            self.api = OsmApi(
                api=self.api_base,
                username="testuser",
                password="testpassword",
                session=self.session_mock,
            )
        else:
            self.api = OsmApi(api=self.api_base, session=self.session_mock)

        self.api._get_http_session = mock.Mock(return_value=self.session_mock)
        self.api._session._sleep = mock.Mock()

    def _return_values(self, filenames):
        if filenames is None:
            filenames = [self._testMethodName + ".xml"]

        return_values = []
        for filename in filenames:
            path = os.path.join(__location__, "fixtures", filename)
            try:
                with codecs.open(path, "r", "utf-8") as file:
                    return_values.append(file.read())
            except Exception:
                pass
        return return_values

    def teardown(self):
        pass

    def test_constructor(self):
        self.assertTrue(isinstance(self.api, OsmApi))
