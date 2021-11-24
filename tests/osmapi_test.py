from __future__ import unicode_literals
from osmapi import OsmApi
import mock
import os
import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


class TestOsmApi(unittest.TestCase):
    def setUp(self):
        self.api_base = "http://api06.dev.openstreetmap.org"
        self.api = OsmApi(
            api=self.api_base
        )
        self.maxDiff = None
        print(self._testMethodName)
        print(self.api)

    def _session_mock(self, auth=False, filenames=None, status=200):
        if auth:
            self.api._username = 'testuser'
            self.api._password = 'testpassword'

        response_mock = mock.Mock()
        response_mock.status_code = status
        return_values = self._return_values(filenames)
        print(filenames)
        print(return_values)
        assert len(return_values) < 2
        if return_values:
            response_mock.content = return_values[0]

        session_mock = mock.Mock()
        session_mock.request = mock.Mock(return_value=response_mock)

        self.api._get_http_session = mock.Mock(return_value=session_mock)
        self.api._session = session_mock

        self.api._sleep = mock.Mock()

    def _return_values(self, filenames):
        if filenames is None:
            filenames = [self._testMethodName + ".xml"]

        return_values = []
        for filename in filenames:
            path = os.path.join(
                __location__,
                'fixtures',
                filename
            )
            try:
                with open(path) as file:
                    return_values.append(file.read())
            except Exception:
                pass
        return return_values

    def teardown(self):
        pass

    def test_constructor(self):
        self.assertTrue(isinstance(self.api, OsmApi))
