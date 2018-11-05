osmapi
======

[![Build](https://img.shields.io/travis/metaodi/osmapi/develop.svg)](https://travis-ci.org/metaodi/osmapi)
[![Coverage](https://img.shields.io/coveralls/metaodi/osmapi/develop.svg)](https://coveralls.io/r/metaodi/osmapi?branch=develop)
[![Version](https://img.shields.io/pypi/v/osmapi.svg)](https://pypi.python.org/pypi/osmapi/)
[![License](https://img.shields.io/pypi/l/osmapi.svg)](https://github.com/metaodi/osmapi/blob/master/LICENSE.txt)

Python wrapper for the OSM API

## Installation

Install [`osmapi` from PyPi](https://pypi.python.org/pypi/osmapi) by using pip: 

    pip install osmapi

## Documentation

The documentation is generated using `pdoc` and can be [viewed online](http://osmapi.metaodi.ch).

The build the documentation locally, you can use

    pdoc --html osmapi.OsmApi # create HTML file

This project uses GitHub Pages to publish its documentation.
To update the online documentation, you need to re-generate the documentation with the above command and update the `gh-pages` branch of this repository.

## Examples

To test this library, please create an account on the [development server of OpenStreetMap (https://api06.dev.openstreetmap.org)](https://api06.dev.openstreetmap.org).

### Read from OpenStreetMap

```python
import osmapi
api = osmapi.OsmApi()
print(api.NodeGet(123))
# {u'changeset': 532907, u'uid': 14298,
# u'timestamp': u'2007-09-29T09:19:17Z',
# u'lon': 10.790009299999999, u'visible': True,
# u'version': 1, u'user': u'Mede',
# u'lat': 59.9503044, u'tag': {}, u'id': 123}
```

### Constructor

```python
import osmapi
api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org", username = "you", password = "***")
api = osmapi.OsmApi(username = "you", passwordfile = "/etc/mypasswords")
api = osmapi.OsmApi(passwordfile = "/etc/mypasswords") # if only the passwordfile is specified, the credentials on the first line of the file will be used
```

Note: Each line in the password file should have the format _user:password_

### Write to OpenStreetMap

```python
import osmapi
api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org", username = u"metaodi", password = u"*******")
api.ChangesetCreate({u"comment": u"My first test"})
print(api.NodeCreate({u"lon":1, u"lat":1, u"tag": {}}))
# {u'changeset': 532907, u'lon': 1, u'version': 1, u'lat': 1, u'tag': {}, u'id': 164684}
api.ChangesetClose()
```

## Note

Scripted imports and automated edits should only be carried out by those with experience and understanding of the way the OpenStreetMap community creates maps, and only with careful **planning** and **consultation** with the local community.

See the [Import/Guidelines](http://wiki.openstreetmap.org/wiki/Import/Guidelines) and [Automated Edits/Code of Conduct](http://wiki.openstreetmap.org/wiki/Automated_Edits/Code_of_Conduct) for more information.

### Development

If you want to help with the development of `osmapi`, you should clone this repository and install the requirements:

    pip install -r requirements.txt
    pip install -r test-requirements.txt

After that, it is recommended to install the `flake8` pre-commit-hook:

    flake8 --install-hook

### Tests

To run the tests use the following command:

    nosetests --verbose

By using tox you can even run the tests against different versions of python (2.7, 3.4, 3.5, 3.6 and 3.7):

    tox

## Release

To create a new release, follow these steps (please respect [Semantic Versioning](http://semver.org/)):

1. Adapt the version number in `osmapi/__init__.py`
1. Update the CHANGELOG with the version
1. Create a pull request to merge develop into master (make sure the tests pass!)
1. Create a [new release/tag on GitHub](https://github.com/metaodi/osmapi/releases) (on the master branch)
1. The [publication on PyPI](https://pypi.python.org/pypi/osmapi) happens via [Travis CI](https://travis-ci.org/metaodi/osmapi) on every tagged commit
1. Re-build the documentation (see above) and copy the generated file to `index.html` on the `gh-pages` branch

## Attribution

This project was orginally developed by Etienne Chové.
This repository is a copy of the original code from SVN (http://svn.openstreetmap.org/applications/utils/python_lib/OsmApi/OsmApi.py), with the goal to enable easy contribution via GitHub and release of this package via [PyPI](https://pypi.python.org/pypi/osmapi).

See also the OSM wiki: http://wiki.openstreetmap.org/wiki/Osmapi
