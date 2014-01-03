from nose.tools import *  # noqa
import osmapi


def setup():
    pass


def teardown():
    pass


def test_constructor():
    api = osmapi.OsmApi()
    assert_true(isinstance(api, osmapi.OsmApi))
