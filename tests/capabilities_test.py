from __future__ import (unicode_literals, absolute_import)
from . import osmapi_test


class TestOsmApiNode(osmapi_test.TestOsmApi):
    def test_Capabilities(self):
        self._session_mock()

        result = self.api.Capabilities()
        self.assertEqual(result, {
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
