import sys

# import backported unit tests for Python 2.6
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from nose.plugins.skip import SkipTest

# import hypothesis
if sys.version_info < (2, 7):
    def given(*args, **kwargs):
        def inner(*args, **kwargs):
            raise SkipTest
        return inner

    def floats(**kwargs):
        pass

    def integers(**kwargs):
        pass
else:
    from hypothesis import given
    from hypothesis.strategies import integers, floats
