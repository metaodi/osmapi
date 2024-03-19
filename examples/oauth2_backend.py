# This script shows how to authenticate with OAuth2 with a backend application
# The token is saved to disk in $HOME/.osmapi/token.json
# It can be reused until it's revoked or expired.

# install oauthlib for requests:  pip install oauthlib requests-oauthlib
from requests_oauthlib import OAuth2Session
import json
import webbrowser
import osmapi
from dotenv import load_dotenv, find_dotenv
import os
import sys

load_dotenv(find_dotenv())

# Credentials you get from registering a new application
# register here: https://master.apis.dev.openstreetmap.org/oauth2/applications
# or on production: https://www.openstreetmap.org/oauth2/applications
client_id = os.getenv("OSM_OAUTH_CLIENT_ID")
client_secret = os.getenv("OSM_OAUTH_CLIENT_SECRET")

# special value for redirect_uri for non-web applications
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

authorization_base_url = "https://master.apis.dev.openstreetmap.org/oauth2/authorize"
token_url = "https://master.apis.dev.openstreetmap.org/oauth2/token"
scope = ["write_api", "write_notes"]


def get_osmapi_path():
    base_dir = ""

    if os.getenv("HOME"):
        base_dir = os.getenv("HOME")
    elif os.getenv("HOMEDRIVE") and os.getenv("HOMEPATH"):
        base_dir = os.path.join(os.getenv("HOMEDRIVE"), os.getenv("HOMEPATH"))
    elif os.getenv("USERPROFILE"):
        base_dir = os.getenv("USERPROFILE")

    if not base_dir:
        print(
            "Unable to find home directory (check env vars HOME, HOMEDRIVE, HOMEPATH and USERPROFILE)",  # noqa
            file=sys.stderr,
        )
        raise Exception("Home directory not found")

    return os.path.join(base_dir, ".osmapi")


def token_saver(token):
    osmapi_path = get_osmapi_path()
    token_path = os.path.join(osmapi_path, "token.json")

    with open(token_path, "w") as f:
        print(f"Saving token {token} to {token_path}")
        f.write(json.dumps(token))


def token_loader():
    osmapi_path = get_osmapi_path()
    token_path = os.path.join(osmapi_path, "token.json")

    with open(token_path, "r") as f:
        token = json.loads(f.read())
        print(f"Loaded token {token} from {token_path}")
    return token


def save_and_get_access_token(client_id, client_secret, redirect_uri, scope):
    oauth = OAuth2Session(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
    )

    login_url, _ = oauth.authorization_url(authorization_base_url)

    print(f"Authorize user using this URL: {login_url}")
    webbrowser.open(login_url)

    authorization_code = input("Paste the authorization code here: ")

    token = oauth.fetch_token(
        token_url=token_url,
        client_secret=client_secret,
        code=authorization_code,
    )

    token_saver(token)
    return token


def make_osm_change(oauth_session):
    api = osmapi.OsmApi(
        api="https://api06.dev.openstreetmap.org", session=oauth_session
    )
    with api.Changeset({"comment": "My first test"}) as changeset_id:
        print(f"Part of Changeset {changeset_id}")
        node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
        print(node1)


# load a previously saved token
try:
    token = token_loader()
except FileNotFoundError:
    print("Token not found, get a new one...")
    token = save_and_get_access_token(client_id, client_secret, redirect_uri, scope)

# test the token
try:
    oauth_session = OAuth2Session(client_id, token=token)
    make_osm_change(oauth_session)
except osmapi.errors.UnauthorizedApiError:
    print("Token expired, let's create a new one")
    token = save_and_get_access_token(client_id, client_secret, redirect_uri, scope)
    oauth_session = OAuth2Session(client_id, token=token)
    make_osm_change(oauth_session)
