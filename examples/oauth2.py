# install oauthlib for requests:  pip install requests-oauth2client
from requests_oauth2client import OAuth2Client, OAuth2AuthorizationCodeAuth
import requests
import webbrowser
import osmapi
from dotenv import load_dotenv, find_dotenv
import os

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

oauth2client = OAuth2Client(
    token_endpoint=token_url,
    authorization_endpoint=authorization_base_url,
    redirect_uri=redirect_uri,
    auth=(client_id, client_secret),
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
api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org", session=oauth_session)
with api.Changeset({"comment": "My first test"}) as changeset_id:
    print(f"Part of Changeset {changeset_id}")
    node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
    print(node1)
