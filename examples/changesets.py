import osmapi
from pprint import pprint

api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org")

try:
    api.ChangesetGet(111111111111)
except osmapi.ApiError as e:
    print(f"Error: {e}")
    if e.status == 404:
        print("Changeset not found")

print("")
pprint(api.ChangesetGet(12345))
