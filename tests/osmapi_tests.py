from nose.tools import *  # noqa
import unittest
import mock
import osmapi
import os

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


class TestOsmApi(unittest.TestCase):
    def setUp(self):
        self.api = osmapi.OsmApi(
            api="api06.dev.openstreetmap.org"
        )

    def _http_mock(self, filename=None, destructor=True):
        if filename is None:
            filename = os.path.join(
                __location__,
                self._testMethodName + ".xml"
            )
        try:
            with open(filename) as file:
                self.api._http_request = mock.Mock(
                    return_value=file.read()
                )
        except:
            pass

        if not destructor:
            self.disable_destructor()

    def disable_destructor(self):
        self.api.__del__ = mock.Mock(
            return_value=None
        )

    def teardown(self):
        pass

    def test_constructor(self):
        assert_true(isinstance(self.api, osmapi.OsmApi))
