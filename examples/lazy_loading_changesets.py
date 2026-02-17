#!/usr/bin/env python3
"""
Example demonstrating lazy loading of changesets using osmapi.

When there are more than 100 changesets matching the query, the OSM API
returns results in batches of up to 100 items. The ChangesetsGet method
with lazy_load=True (default) automatically handles pagination, fetching
additional batches as needed.

This example shows how to:
1. Get changesets with automatic lazy loading (default behavior)
2. Iterate through all changesets without loading all data upfront
3. Access specific changesets by ID
4. Convert to a regular dict when needed
"""

import osmapi

# Create an API client
api = osmapi.OsmApi()

print("Example 1: Lazy loading (default behavior)")
print("=" * 60)

# Get changesets for a user - returns a ChangesetsResponse object
# Only the first batch (up to 100 changesets) is loaded immediately
result = api.ChangesetsGet(username="metaodi")

# The response object behaves like a dict
print(f"Type: {type(result)}")
print(f"Number of changesets loaded so far: {len(result)}")

# Accessing a specific changeset by ID
# If it's not in the loaded data, more batches will be fetched automatically
if len(result) > 0:
    first_id = list(result.keys())[0]
    print(f"\nFirst changeset ID: {first_id}")
    print(f"Changeset data: {result[first_id]}")

print("\n" + "=" * 60)
print("Example 2: Iterating through all changesets")
print("=" * 60)

# When iterating, additional batches are loaded automatically as needed
count = 0
for changeset_id in result:
    count += 1
    if count <= 3:
        print(f"Changeset {changeset_id}: {result[changeset_id].get('created_at')}")
    elif count == 4:
        print("...")

print(f"\nTotal changesets iterated: {count}")

print("\n" + "=" * 60)
print("Example 3: Dict-like operations")
print("=" * 60)

# You can use dict methods like keys(), values(), items()
# These load all remaining data
print(f"Keys: {list(result.keys())[:5]}...")
print(f"Has specific ID: {first_id in result}")

# Get with default value
print(f"Get non-existent: {result.get(99999999, 'Not found')}")

print("\n" + "=" * 60)
print("Example 4: Convert to regular dict")
print("=" * 60)

# If you need a regular dict (e.g., for serialization), use as_dict()
regular_dict = result.as_dict()
print(f"Type after conversion: {type(regular_dict)}")
print(f"Number of changesets: {len(regular_dict)}")

print("\n" + "=" * 60)
print("Example 5: Disable lazy loading (backward compatibility)")
print("=" * 60)

# If you want the old behavior (load once, return dict), use lazy_load=False
# This will only return the first batch (up to 100 changesets)
result_eager = api.ChangesetsGet(username="metaodi", lazy_load=False)
print(f"Type: {type(result_eager)}")
print(f"Number of changesets: {len(result_eager)}")
print("Note: With lazy_load=False, you only get the first 100 changesets")

print("\n" + "=" * 60)
print("Example 6: Filter by other criteria")
print("=" * 60)

# You can combine filters - lazy loading works with all parameters
result_filtered = api.ChangesetsGet(
    username="metaodi",
    only_closed=True,
    # closed_after="2020-01-01T00:00:00Z",
)
print(f"Filtered changesets: {len(result_filtered)} (first batch loaded)")

# Clean up
api.close()

print("\n" + "=" * 60)
print("Example complete!")
print("=" * 60)
