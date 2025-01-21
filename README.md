osmapi
======

[![Build osmapi](https://github.com/metaodi/osmapi/actions/workflows/build.yml/badge.svg)](https://github.com/metaodi/osmapi/actions/workflows/build.yml)
[![Version](https://img.shields.io/pypi/v/osmapi.svg)](https://pypi.python.org/pypi/osmapi/)
[![License](https://img.shields.io/pypi/l/osmapi.svg)](https://github.com/metaodi/osmapi/blob/develop/LICENSE.txt)
[![Coverage](https://img.shields.io/coveralls/metaodi/osmapi/develop.svg)](https://coveralls.io/r/metaodi/osmapi?branch=develop)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)


Python wrapper for the OSM API (requires Python >= 3.8)

## Installation

Install [`osmapi` from PyPi](https://pypi.python.org/pypi/osmapi) by using pip: 

    pip install osmapi

## Documentation

The documentation is generated using `pdoc` and can be [viewed online](http://osmapi.metaodi.ch).

The build the documentation locally, you can use

    make docs

This project uses GitHub Pages to publish its documentation.
To update the online documentation, you need to re-generate the documentation with the above command and update the `main` branch of this repository.

## Examples

To test this library, please create an account on the [development server of OpenStreetMap (https://api06.dev.openstreetmap.org)](https://api06.dev.openstreetmap.org).

Check the [examples directory](https://github.com/metaodi/osmapi/tree/develop/examples) to find more example code.

### Read from OpenStreetMap

```python
>>> import osmapi
>>> api = osmapi.OsmApi()
>>> print(api.NodeGet(123))
{'changeset': 532907, 'uid': 14298,
'timestamp': '2007-09-29T09:19:17Z',
'lon': 10.790009299999999, 'visible': True,
'version': 1, 'user': 'Mede',
'lat': 59.9503044, 'tag': {}, 'id': 123}
```

### Write to OpenStreetMap

```python
>>> import osmapi
>>> api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org", username = "metaodi", password = "*******")
>>> api.ChangesetCreate({"comment": "My first test"})
>>> print(api.NodeCreate({"lon":1, "lat":1, "tag": {}}))
{'changeset': 532907, 'lon': 1, 'version': 1, 'lat': 1, 'tag': {}, 'id': 164684}
>>> api.ChangesetClose()
```

### OAuth authentication

Username/Password authentication will be deprecated in July 2024
(see [official OWG announcemnt](https://blog.openstreetmap.org/2024/04/17/oauth-1-0a-and-http-basic-auth-shutdown-on-openstreetmap-org/) for details).
In order to use this library in the future, you'll need to use OAuth 2.0.

To use OAuth 2.0, you must register an application with an OpenStreetMap account, either on the
[development server](https://master.apis.dev.openstreetmap.org/oauth2/applications)
or on the [production server](https://www.openstreetmap.org/oauth2/applications).
Once this registration is done, you'll get a `client_id` and a `client_secret` that you can use to authenticate users.

Example code using [`cli-oauth2`](https://github.com/Zverik/cli-oauth2) on the development server, replace `OpenStreetMapDevAuth` with `OpenStreetMapAuth` to use the production server:

```python
import osmapi
from oauthcli import OpenStreetMapDevAuth

client_id = "<client_id>"
client_secret = "<client_secret>"

auth = OpenStreetMapDevAuth(
    client_id, client_secret, ['read_prefs', 'write_map']
).auth_code()

api = osmapi.OsmApi(
    api="https://api06.dev.openstreetmap.org",
    session=auth.session
)

with api.Changeset({"comment": "My first test"}) as changeset_id:
    print(f"Part of Changeset {changeset_id}")
    node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
    print(node1)
```

An alternative way using the `requests-oauthlib` library can be found
[in the examples](https://github.com/metaodi/osmapi/blob/develop/examples/oauth2.py).


### User agent / credit for application

To credit the application that supplies changes to OSM, an `appid` can be provided.
This is a string identifying the application.
If this is omitted "osmapi" is used.

```python
api = osmapi.OsmApi(
    api="https://api06.dev.openstreetmap.org",
    appid="MyOSM Script"
)
```

 If then changesets are made using this osmapi instance, they get a tag `created_by` with the following content: `MyOSM Script (osmapi/<version>)` 
 
 [Example changeset of `Kort` using osmapi](https://www.openstreetmap.org/changeset/55197785)

## Note about imports / automated edits

Scripted imports and automated edits should only be carried out by those with experience and understanding of the way the OpenStreetMap community creates maps, and only with careful **planning** and **consultation** with the local community.

See the [Import/Guidelines](http://wiki.openstreetmap.org/wiki/Import/Guidelines) and [Automated Edits/Code of Conduct](http://wiki.openstreetmap.org/wiki/Automated_Edits/Code_of_Conduct) for more information.

## Development

If you want to help with the development of `osmapi`, you should clone this repository and install the requirements:

    make deps

Better yet use the provided [`setup.sh`](https://github.com/metaodi/osmapi/blob/develop/setup.sh) script to create a virtual env and install this package in it. 

You can lint the source code using this command:

    make lint

And if you want to reformat the files (using the black code style) simply run:

    make format

To run the tests use the following command:

    make test

## Release

To create a new release, follow these steps (please respect [Semantic Versioning](http://semver.org/)):

1. Adapt the version number in `osmapi/__init__.py`
1. Update the CHANGELOG with the version
1. Re-build the documentation (`make docs`)
1. Create a [pull request to merge develop into main](https://github.com/metaodi/osmapi/compare/main...develop) (make sure the tests pass!)
1. Create a [new release/tag on GitHub](https://github.com/metaodi/osmapi/releases) (on the main branch)
1. The [publication on PyPI](https://pypi.python.org/pypi/osmapi) happens via [GitHub Actions](https://github.com/metaodi/osmapi/actions/workflows/publish_python.yml) on every tagged commit

## Attribution

This project was orginally developed by Etienne Chové.
This repository is a copy of the original code from SVN (http://svn.openstreetmap.org/applications/utils/python_lib/OsmApi/OsmApi.py), with the goal to enable easy contribution via GitHub and release of this package via [PyPI](https://pypi.python.org/pypi/osmapi).

See also the OSM wiki: http://wiki.openstreetmap.org/wiki/Osmapi
