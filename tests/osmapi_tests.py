from __future__ import unicode_literals
from nose.tools import *  # noqa
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
        self.api = OsmApi(
            api="api06.dev.openstreetmap.org"
        )
        self.maxDiff = None
        print(self._testMethodName)
        print(self.api)

    def _conn_mock(self, auth=False, filenames=None, status=200, reason=None):
        if auth:
            self.api._username = 'testuser'
            self.api._password = 'testpassword'

        response_mock = mock.Mock()
        response_mock.status = status
        response_mock.reason = reason
        response_mock.read = mock.Mock(
            side_effect=self._return_values(filenames)
        )

        conn_mock = mock.Mock()
        conn_mock.putrequest = mock.Mock()
        conn_mock.putheader = mock.Mock()
        conn_mock.endheaders = mock.Mock()
        conn_mock.send = mock.Mock()
        conn_mock.getresponse = mock.Mock(return_value=response_mock)

        self.api._get_http_connection = mock.Mock(return_value=conn_mock)
        self.api._conn = conn_mock

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
            except:
                pass
        return return_values

    def teardown(self):
        pass

    def test_constructor(self):
        assert_true(isinstance(self.api, OsmApi))
