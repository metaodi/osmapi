from __future__ import (unicode_literals, absolute_import)
from nose.tools import *  # noqa
from . import osmapi_tests
from . import given, integers, floats


class TestOsmApiNode(osmapi_tests.TestOsmApi):
    def test_Capabilities(self):
        self._conn_mock()

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

    @given(
        floats(min_value=0.0),
        floats(min_value=0.0),
        floats(min_value=0.0),
        integers(min_value=0),
        integers(min_value=0),
        integers(min_value=0),
        integers(min_value=0)
    )
    def test_Capabilities_template(self, minVersion, maxVersion, maxArea,
                                   tpPage, maxWayNodes, maxElements, timeout):
        args = {
            'minVersion': minVersion,
            'maxVersion': maxVersion,
            'maxArea': maxArea,
            'tracepointsPerPage': tpPage,
            'maxWayNodes': maxWayNodes,
            'maxElements': maxElements,
            'timeout': timeout,
        }
        self._conn_mock(args=args)

        result = self.api.Capabilities()
        assert_greater_equal(result['area']['maximum'], 0.0)
        assert_greater_equal(result['changesets']['maximum_elements'], 0.0)
        assert_true(result['status']['api'])
        assert_true(result['status']['database'])
        assert_true(result['status']['gpx'])
        assert_greater_equal(result['timeout']['seconds'], 0)
        assert_greater_equal(result['tracepoints']['per_page'], 0)
        assert_greater_equal(result['version']['maximum'], 0.0)
        assert_greater_equal(result['version']['minimum'], 0.0)
        assert_greater_equal(result['waynodes']['maximum'], 0)
