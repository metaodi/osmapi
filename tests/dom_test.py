from . import osmapi_test
import osmapi
import mock
import datetime


class TestOsmApiDom(osmapi_test.TestOsmApi):
    def test_DomGetAttributes(self):
        mock_domelement = mock.Mock()
        mock_domelement.attributes = {
            'uid': '12345',
            'open': 'false',
            'visible': 'true',
            'lat': '47.1234',
            'date': '2021-12-10T21:28:03Z',
            'new_attribute': 'Test 123',
        }

        result = osmapi.dom._DomGetAttributes(mock_domelement)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['uid'], 12345)
        self.assertEqual(result['open'], False)
        self.assertEqual(result['visible'], True)
        self.assertEqual(result['lat'], 47.1234)
        self.assertEqual(result['date'], datetime.datetime(2021, 12, 10, 21, 28, 3))
        self.assertEqual(result['new_attribute'], 'Test 123')
