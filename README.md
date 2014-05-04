osmapi
======

[![Build](https://travis-ci.org/metaodi/osmapi.png?branch=develop)](https://travis-ci.org/metaodi/osmapi)
[![Coverage](https://coveralls.io/repos/metaodi/osmapi/badge.png?branch=develop)](https://coveralls.io/r/metaodi/osmapi?branch=develop)
[![Version](https://badge.fury.io/py/osmapi.png)](http://badge.fury.io/py/osmapi)
[![Downloads](https://pypip.in/d/osmapi/badge.png)](https://pypi.python.org/pypi/osmapi/)
[![License](https://pypip.in/license/osmapi/badge.png)](https://pypi.python.org/pypi/osmapi/)

Python wrapper for the OSM API

## Installation

Install `osmapi` simply by using pip:

    pip install osmapi

### Development

If you want to help with the development of `osmapi`, you should clone this repository and install the requirements:

    pip install -r requirements.txt
    pip install -r test-requirements.txt

After that, it is recommended to install the `flake8` pre-commit-hook:

    flake8 --install-hook

### Tests

To run the tests use the following command:

    nosetests --verbose

By using tox you can even run the tests against different versions of python (2.6, 2.7, 3.2 and 3.3):

    tox

## Note

Scripted imports and automated edits should only be carried out by those with experience and understanding of the way the OpenStreetMap community creates maps, and only with careful **planning** and **consultation** with the local community.

See the [Import/Guidelines](http://wiki.openstreetmap.org/wiki/Import/Guidelines) and [Automated Edits/Code of Conduct](http://wiki.openstreetmap.org/wiki/Automated_Edits/Code_of_Conduct) for more information.

## Examples

### Read from OpenStreetMap

```python
import osmapi
api = osmapi.OsmApi()
print api.NodeGet(123)
# {u'changeset': 532907, u'uid': 14298,
# u'timestamp': u'2007-09-29T09:19:17Z',
# u'lon': 10.790009299999999, u'visible': True,
# u'version': 1, u'user': u'Mede',
# u'lat': 59.9503044, u'tag': {}, u'id': 123}
```

### Constructor

```python
import osmapi
api = osmapi.OsmApi(api="api06.dev.openstreetmap.org", username = "you", password = "***")
api = osmapi.OsmApi(username = "you", passwordfile = "/etc/mypasswords")
api = osmapi.OsmApi(passwordfile = "/etc/mypasswords") # username will be first line username
```

Note: The password file should have the format _user:password_

### Write to OpenStreetMap

```python
import osmapi
api = osmapi.OsmApi(username = u"metaodi", password = u"*******")
api.ChangesetCreate({u"comment": u"My first test"})
print api.NodeCreate({u"lon":1, u"lat":1, u"tag": {}})
# {u'changeset': 532907, u'lon': 1, u'version': 1, u'lat': 1, u'tag': {}, u'id': 164684}
api.ChangesetClose()
```

## Attribution

This project was orginally developed by Etienne Chové.
This repository is a copy of the original code from SVN (http://svn.openstreetmap.org/applications/utils/python_lib/OsmApi/OsmApi.py), with the goal to enable easy contribution via GitHub and release of this package via [PyPI](https://pypi.python.org/pypi/osmapi).

See also the OSM wiki: http://wiki.openstreetmap.org/wiki/Osmapi
