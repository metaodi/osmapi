from . import osmapi_test
import osmapi
from unittest import mock
import datetime


class TestOsmApiDom(osmapi_test.TestOsmApi):
    def test_DomGetAttributes(self):
        mock_domelement = mock.Mock()
        mock_domelement.attributes = {
            "uid": "12345",
            "open": "false",
            "visible": "true",
            "lat": "47.1234",
            "date": "2021-12-10T21:28:03Z",
            "new_attribute": "Test 123",
        }

        result = osmapi.dom._DomGetAttributes(mock_domelement)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["uid"], 12345)
        self.assertEqual(result["open"], False)
        self.assertEqual(result["visible"], True)
        self.assertEqual(result["lat"], 47.1234)
        self.assertEqual(result["date"], datetime.datetime(2021, 12, 10, 21, 28, 3))
        self.assertEqual(result["new_attribute"], "Test 123")

    def test_ParseDate(self):
        self.assertEqual(
            osmapi.dom._ParseDate("2021-02-25T09:49:33Z"),
            datetime.datetime(2021, 2, 25, 9, 49, 33),
        )
        self.assertEqual(
            osmapi.dom._ParseDate("2021-02-25 09:49:33 UTC"),
            datetime.datetime(2021, 2, 25, 9, 49, 33),
        )
        with self.assertLogs("osmapi.dom", level="DEBUG") as cm:
            self.assertEqual(osmapi.dom._ParseDate("2021-02-25"), "2021-02-25")
            self.assertEqual(osmapi.dom._ParseDate(""), "")
            self.assertIsNone(osmapi.dom._ParseDate(None))

            # test logging output
            self.assertEqual(
                cm.output,
                [
                    "DEBUG:osmapi.dom:2021-02-25 does not match %Y-%m-%d %H:%M:%S UTC",
                    "DEBUG:osmapi.dom:2021-02-25 does not match %Y-%m-%dT%H:%M:%SZ",
                    "DEBUG:osmapi.dom: does not match %Y-%m-%d %H:%M:%S UTC",
                    "DEBUG:osmapi.dom: does not match %Y-%m-%dT%H:%M:%SZ",
                    "DEBUG:osmapi.dom:None does not match %Y-%m-%d %H:%M:%S UTC",
                    "DEBUG:osmapi.dom:None does not match %Y-%m-%dT%H:%M:%SZ",
                ],
            )
