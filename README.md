osmapi
======

[![Build osmapi](https://github.com/metaodi/osmapi/actions/workflows/build.yml/badge.svg)](https://github.com/metaodi/osmapi/actions/workflows/build.yml)
[![Version](https://img.shields.io/pypi/v/osmapi.svg)](https://pypi.python.org/pypi/osmapi/)
[![License](https://img.shields.io/pypi/l/osmapi.svg)](https://github.com/metaodi/osmapi/blob/master/LICENSE.txt)
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
To update the online documentation, you need to re-generate the documentation with the above command and update the `master` branch of this repository.

## Examples

To test this library, please create an account on the [development server of OpenStreetMap (https://api06.dev.openstreetmap.org)](https://api06.dev.openstreetmap.org).

Check the [examples directory](https://github.com/metaodi/osmapi/tree/develop/examples) to find more example code.

### Read from OpenStreetMap

```python
>>> import osmapi
>>> api = osmapi.OsmApi()
>>> print(api.NodeGet(123))
{u'changeset': 532907, u'uid': 14298,
u'timestamp': u'2007-09-29T09:19:17Z',
u'lon': 10.790009299999999, u'visible': True,
u'version': 1, u'user': u'Mede',
u'lat': 59.9503044, u'tag': {}, u'id': 123}
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
>>> import osmapi
>>> api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org", username = u"metaodi", password = u"*******")
>>> api.ChangesetCreate({u"comment": u"My first test"})
>>> print(api.NodeCreate({u"lon":1, u"lat":1, u"tag": {}}))
{u'changeset': 532907, u'lon': 1, u'version': 1, u'lat': 1, u'tag': {}, u'id': 164684}
>>> api.ChangesetClose()
```

### OAuth authentication

Username/Password authentication will be deprecated in 2024 (see [official OWG announcemnt](https://www.openstreetmap.org/user/pnorman/diary/401157) for details).
In order to use this library in the future, you'll need to use OAuth 2.0.

To use OAuth 2.0, you must register an application with an OpenStreetMap account, either on the [development server](https://master.apis.dev.openstreetmap.org/oauth2/applications) or on the [production server](https://www.openstreetmap.org/oauth2/applications).
Once this registration is done, you'll get a `client_id` and a `client_secret` that you can use to authenticate users.

Example code using [`requests-oauth2client`](https://pypi.org/project/requests-oauth2client/):

```python
from requests_oauth2client import OAuth2Client, OAuth2AuthorizationCodeAuth
import requests
import webbrowser
import osmapi
import os

client_id = "<client_id>"
client_secret = "<client_secret>"

# special value for redirect_uri for non-web applications
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

authorization_base_url = "https://master.apis.dev.openstreetmap.org/oauth2/authorize"
token_url = "https://master.apis.dev.openstreetmap.org/oauth2/token"

oauth2client = OAuth2Client(
    token_endpoint=token_url,
    authorization_endpoint=authorization_base_url,
    redirect_uri=redirect_uri,
    client_id=client_id,
    client_secret=client_secret,
    code_challenge_method=None,
)

# open OSM website to authrorize user using the write_api and write_notes scope
scope = ["write_api", "write_notes"]
az_request = oauth2client.authorization_request(scope=scope)
print(f"Authorize user using this URL: {az_request.uri}")
webbrowser.open(az_request.uri)

# create a new requests session using the OAuth authorization
auth_code = input("Paste the authorization code here: ")
auth = OAuth2AuthorizationCodeAuth(
    oauth2client,
    auth_code,
    redirect_uri=redirect_uri,
)
oauth_session = requests.Session()
oauth_session.auth = auth

# use the custom session
api = osmapi.OsmApi(
    api="https://api06.dev.openstreetmap.org",
    session=oauth_session
)
with api.Changeset({"comment": "My first test"}) as changeset_id:
    print(f"Part of Changeset {changeset_id}")
    node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
    print(node1)
```

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
1. Create a pull request to merge develop into master (make sure the tests pass!)
1. Create a [new release/tag on GitHub](https://github.com/metaodi/osmapi/releases) (on the master branch)
1. The [publication on PyPI](https://pypi.python.org/pypi/osmapi) happens via [GitHub Actions](https://github.com/metaodi/osmapi/actions/workflows/publish_python.yml) on every tagged commit

## Attribution

This project was orginally developed by Etienne Chové.
This repository is a copy of the original code from SVN (http://svn.openstreetmap.org/applications/utils/python_lib/OsmApi/OsmApi.py), with the goal to enable easy contribution via GitHub and release of this package via [PyPI](https://pypi.python.org/pypi/osmapi).

See also the OSM wiki: http://wiki.openstreetmap.org/wiki/Osmapi
