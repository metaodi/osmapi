from __future__ import unicode_literals
from nose.tools import *  # noqa
from osmapi import OsmApi
import mock
import os
import sys
import pystache

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


class TestOsmApi(unittest.TestCase):
    def setUp(self):
        self.api = OsmApi(
            api="api06.dev.openstreetmap.org"
        )
        self.maxDiff = None
        print(self._testMethodName)
        print(self.api)

    def _conn_mock(self, auth=False, filenames=None,
                   status=200, reason=None, args=None):
        if auth:
            self.api._username = 'testuser'
            self.api._password = 'testpassword'

        if args is not None:
            response_mock = self._response_mock_from_template(
                status,
                reason,
                filenames,
                args
            )
        else:
            response_mock = self._response_mock_from_fixture(
                status,
                reason,
                filenames
            )

        conn_mock = mock.Mock()
        conn_mock.putrequest = mock.Mock()
        conn_mock.putheader = mock.Mock()
        conn_mock.endheaders = mock.Mock()
        conn_mock.send = mock.Mock()
        conn_mock.getresponse = mock.Mock(return_value=response_mock)

        self.api._get_http_connection = mock.Mock(return_value=conn_mock)
        self.api._conn = conn_mock

        self.api._sleep = mock.Mock()

    def _response_mock_from_fixture(self, status, reason, filenames):
        response_mock = mock.Mock()
        response_mock.status = status
        response_mock.reason = reason
        response_mock.read = mock.Mock(
            side_effect=self._return_fixture_values(filenames)
        )
        return response_mock

    def _response_mock_from_template(self, status, reason, filenames, args):
        response_mock = mock.Mock()
        response_mock.status = status
        response_mock.reason = reason
        response_mock.read = mock.Mock(
            side_effect=self._return_template_values(filenames, args)
        )
        return response_mock

    def _return_fixture_values(self, filenames):
        if filenames is None:
            filenames = [self._testMethodName + ".xml"]

        return_values = []
        for filename in filenames:
            path = os.path.join(
                __location__,
                'fixtures',
                filename
            )
            try:
                with open(path) as file:
                    return_values.append(file.read())
            except:
                pass
        return return_values

    def _return_template_values(self, templates, args):
        if templates is None:
            templates = [self._testMethodName + ".xml"]

        return_values = []
        for filename in templates:
            path = os.path.join(
                __location__,
                'templates',
                filename
            )
            try:
                with open(path) as file:
                    rendered_values = pystache.render(
                        file.read(),
                        args
                    )
                    return_values.append(rendered_values)
            except:
                pass
        return return_values

    def teardown(self):
        pass

    def test_constructor(self):
        assert_true(isinstance(self.api, OsmApi))
