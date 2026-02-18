from . import osmapi_test


class TestOsmApiNode(osmapi_test.TestOsmApi):
    def test_capabilities(self):
        self._session_mock()
        result = self.api.capabilities()
        self.assertEqual(
            result,
            {
                "area": {"maximum": 0.25},
                "changesets": {"maximum_elements": 50000.0},
                "status": {"api": "mocked", "database": "online", "gpx": "online"},
                "timeout": {"seconds": 300.0},
                "tracepoints": {"per_page": 5000.0},
                "version": {"maximum": 0.6, "minimum": 0.6},
                "waynodes": {"maximum": 2000.0},
            },
        )

    def test_Capabilities_deprecation_warning(self):
        self._session_mock(filenames=["test_Capabilities.xml"])
        with self.assertWarns(DeprecationWarning):
            self.api.Capabilities()
