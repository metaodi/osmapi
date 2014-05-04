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

    def _http_mock(self, filenames=None):
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

        self.api._http_request = mock.Mock()
        self.api._http_request.side_effect = return_values

    def teardown(self):
        pass

    def test_constructor(self):
        assert_true(isinstance(self.api, OsmApi))
