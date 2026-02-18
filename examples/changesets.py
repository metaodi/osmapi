import osmapi
from pprint import pprint


api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org")


try:
    api.changeset_get(111111111111)
except osmapi.ApiError as e:
    print(f"Error: {e}")
    if e.status == 404:
        print("Changeset not found")


print("")
pprint(api.changeset_get(12345))
