from nose.tools import *  # noqa
import osmapi


def setup():
    pass


def teardown():
    pass


def test_constructor():
    api = osmapi.OsmApi()
    assert_is_instance(api, osmapi.OsmApi)
