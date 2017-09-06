import httpretty
import unittest
import osmapi


class TestOsmApiFunctional(unittest.TestCase):
    @httpretty.activate
    def test_deleted_element_raises_exception(self):
        httpretty.HTTPretty.allow_net_connect = False
        httpretty.register_uri(
            httpretty.GET,
            "https://www.openstreetmap.org/api/0.6/relation/2911456/full",
            status=410
        )
        with self.assertRaises(osmapi.ElementDeletedApiError) as context:
            api = osmapi.OsmApi()
            api.RelationFull(2911456)
        self.assertEquals(410, context.exception.status)
