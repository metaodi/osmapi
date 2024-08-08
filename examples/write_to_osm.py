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


api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org", session=auth.session)
with api.Changeset({"comment": "My first test"}) as changeset_id:
    print(f"Part of Changeset {changeset_id}")
    node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
    print(node1)
    node2 = api.NodeCreate({"lon": 2, "lat": 2, "tag": {}})
    print(node2)
    way = api.WayCreate(
        {
            "nd": [
                node1["id"],
                node2["id"],
            ],
            "tag": {
                "highway": "unclassified",
                "name": "Osmapi Street",
            },
        }
    )
    print(way)
