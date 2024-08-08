# install cli-oauth2 for requests:  pip install cli-oauth2
from oauthcli import OpenStreetMapDevAuth
import osmapi
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

# load secrets for OAuth
client_id = os.getenv("OSM_OAUTH_CLIENT_ID")
client_secret = os.getenv("OSM_OAUTH_CLIENT_SECRET")

auth = OpenStreetMapDevAuth(
    client_id, client_secret, ["write_api", "write_notes"]
).auth_code()


# Use a normal timeout (30s is the default value)
normal_timeout_api = osmapi.OsmApi(
    api="https://api06.dev.openstreetmap.org", session=auth.session, timeout=30
)
changeset_id = normal_timeout_api.ChangesetCreate({"comment": "My first test"})
print(f"Create new changeset {changeset_id}")

# Deliberately using a very small timeout to show what happens when a timeout occurs
low_timeout_api = osmapi.OsmApi(
    api="https://api06.dev.openstreetmap.org", session=auth.session, timeout=0.00001
)
try:
    changeset_id = low_timeout_api.ChangesetCreate({"comment": "My first test"})
    print(f"Create new changeset {changeset_id}")
except osmapi.errors.TimeoutApiError as e:
    print(f"Timeout error occured: {str(e)}")
