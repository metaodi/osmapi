from nose.tools import *  # noqa
import mock
import osmapi_tests


class TestOsmApiNode(osmapi_tests.TestOsmApi):
    def test_NodeGet(self):
        self._http_mock()

        result = self.api.NodeGet(123)
        assert_equals(result, {
            u'id': 123,
            u'changeset': 15293,
            u'uid': 605,
            u'timestamp': u'2012-04-18T11:14:26Z',
            u'lat': 51.8753146,
            u'lon': -1.4857118,
            u'visible': True,
            u'version': 8,
            u'user': u'freundchen',
            u'tag': {
                u'amenity': u'school',
                u'foo': u'bar',
                u'name': u'Berolina & Schule'
            },
        })

    def test_NodeCreate_wo_changeset(self):
        test_node = {
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'name': 'pastafarian'
            }
        }

        with self.assertRaisesRegexp(Exception, 'need to open a changeset'):
            self.api.NodeCreate(test_node)

    def test_NodeCreate(self):
        self._http_mock()

        # setup mock
        self.api.ChangesetCreate = mock.Mock(
            return_value=1111
        )
        self.api._CurrentChangesetId = 1111

        test_node = {
            'lat': 47.287,
            'lon': 8.765,
            'tag': {
                'amenity': 'place_of_worship',
                'name': 'pastafarian'
            }
        }

        cs = self.api.ChangesetCreate({
            'comment': 'This is a test dataset'
        })
        assert_equals(cs, 1111)
        result = self.api.NodeCreate(test_node)
        assert_equals(result['id'], 9876)
        assert_equals(result['lat'], test_node['lat'])
        assert_equals(result['lon'], test_node['lon'])
        assert_equals(result['tag'], test_node['tag'])
