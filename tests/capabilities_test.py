from __future__ import unicode_literals
from nose.tools import *  # noqa
import osmapi_tests


class TestOsmApiNode(osmapi_tests.TestOsmApi):
    def test_Capabilities(self):
        self._http_mock()

        result = self.api.Capabilities()
        assert_equals(result, {
            'area': {'maximum': 0.25},
            'changesets': {'maximum_elements': 50000.0},
            'status': {
                'api': 'mocked',
                'database': 'online',
                'gpx': 'online'
            },
            'timeout': {'seconds': 300.0},
            'tracepoints': {'per_page': 5000.0},
            'version': {'maximum': 0.6, 'minimum': 0.6},
            'waynodes': {'maximum': 2000.0}
        })
