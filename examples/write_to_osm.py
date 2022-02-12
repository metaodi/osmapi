import osmapi
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
user = os.getenv('OSM_USER')
pw = os.getenv('OSM_PASS')

api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org", username=user, password=pw)
with api.Changeset({u"comment": u"My first test"}) as changeset_id:
    print(f"Part of Changeset {changeset_id}")
    node1 = api.NodeCreate({u"lon": 1, u"lat": 1, u"tag": {}})
    print(node1)
    node2 = api.NodeCreate({u"lon": 2, u"lat": 2, u"tag": {}})
    print(node2)
    way = api.WayCreate({
        'nd': [
            node1['id'],
            node2['id'],
        ],
        'tag': {
            'highway': 'unclassified',
            'name': 'Osmapi Street',
        }
    })
    print(way)
