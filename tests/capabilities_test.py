from nose.tools import *  # noqa
import osmapi_tests


class TestOsmApiNode(osmapi_tests.TestOsmApi):
    def test_Capabilities(self):
        self._http_mock()

        result = self.api.Capabilities()
        assert_equals(result, {
            u'area': {u'maximum': 0.25},
            u'changesets': {u'maximum_elements': 50000.0},
            u'status': {
                u'api': u'mocked',
                u'database': u'online',
                u'gpx': u'online'
            },
            u'timeout': {u'seconds': 300.0},
            u'tracepoints': {u'per_page': 5000.0},
            u'version': {u'maximum': 0.6, u'minimum': 0.6},
            u'waynodes': {u'maximum': 2000.0}
        })
