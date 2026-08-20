"""Working through a response that is too large to keep in memory.

The history of a much-edited relation, or a `map` call over a busy area, can
be hundreds of megabytes of XML. The regular methods build the complete result
before returning it, so they need memory for all of it at once. Every one of
them has an `_iter` counterpart that yields the same dicts while the response
is still being downloaded, holding only one element at a time.
"""

import osmapi

api = osmapi.OsmApi(api="https://api06.dev.openstreetmap.org")

RELATION_ID = 12345

# The whole history at once — fine for a small relation, expensive for a big one
history = api.relation_history(RELATION_ID)
print(f"{len(history)} versions, latest is v{max(history)}")

# The same data, one version at a time
for version in api.relation_history_iter(RELATION_ID):
    members = len(version["member"])
    print(f"v{version['version']:>4} by {version['user']}: {members} members")

# The iterator can be stopped early; only what was needed is downloaded
for version in api.relation_history_iter(RELATION_ID):
    if version["version"] >= 3:
        break
    print(f"early version: v{version['version']}")

# Counting the elements of a bounding box without collecting any of them
counts: dict[str, int] = {}
for element in api.map_iter(8.765, 47.287, 8.767, 47.289):
    counts[element["type"]] = counts.get(element["type"], 0) + 1
print(counts)

# The same is available for way_full_iter, relation_full_iter,
# node_history_iter, way_history_iter and changeset_download_iter.
api.close()
