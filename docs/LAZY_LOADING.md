# Lazy Loading for Changesets

## Overview

The `ChangesetsGet` method now supports lazy loading to handle queries that return more than 100 changesets. The OpenStreetMap API limits responses to 100 changesets per request, so lazy loading automatically fetches additional batches as needed.

## Usage

### Default Behavior (Lazy Loading Enabled)

By default, `ChangesetsGet` returns a `ChangesetsResponse` object that behaves like a dictionary but loads data on demand:

```python
import osmapi

api = osmapi.OsmApi()

# Returns a ChangesetsResponse object
# Only the first batch (up to 100 changesets) is loaded immediately
changesets = api.ChangesetsGet(username="someuser")

# Accessing data triggers loading of additional batches if needed
for changeset_id in changesets:
    print(f"Changeset {changeset_id}: {changesets[changeset_id]}")
```

### Dict-Like Interface

The `ChangesetsResponse` object supports all standard dictionary operations:

```python
# Length (returns count of currently loaded changesets)
print(len(changesets))

# Iteration (loads additional batches as needed)
for changeset_id in changesets:
    print(changeset_id)

# Key access (loads all data if changeset not found in current batch)
changeset = changesets[12345]

# Contains check
if 12345 in changesets:
    print("Found!")

# Dict methods (load all remaining data)
keys = changesets.keys()
values = changesets.values()
items = changesets.items()

# Get with default
changeset = changesets.get(12345, None)
```

### Converting to Regular Dict

If you need a regular Python dictionary (e.g., for JSON serialization):

```python
# Load all data and return as a regular dict
regular_dict = changesets.as_dict()
```

### Disabling Lazy Loading (Backward Compatibility)

If you want the original behavior (single API call, maximum 100 results):

```python
# Returns a regular dict with only the first batch
changesets = api.ChangesetsGet(username="someuser", lazy_load=False)
```

## Benefits

1. **Automatic Pagination**: No need to manually handle multiple API requests
2. **Memory Efficient**: Data is loaded only when accessed
3. **Backward Compatible**: Existing code continues to work
4. **Transparent**: The response object behaves like a regular dict

## Implementation Details

- **First Batch Loaded Eagerly**: The first batch (up to 100 changesets) is loaded immediately when `ChangesetsGet` is called
- **Subsequent Batches Loaded on Demand**: Additional batches are fetched automatically when you iterate or access data not yet loaded
- **Pagination Strategy**: Uses the timestamp of the last loaded changeset to request the next batch with `order=oldest`
- **End Detection**: Stops loading when a batch returns fewer than 100 changesets

## Example: Loading All Changesets for a User

```python
import osmapi

api = osmapi.OsmApi()

# Get all changesets for a user (may be >100)
changesets = api.ChangesetsGet(username="metaodi")

# Iterate through all changesets - additional batches loaded automatically
for changeset_id, changeset_data in changesets.items():
    print(f"Changeset {changeset_id} created at {changeset_data['created_at']}")

# Total count (all batches loaded at this point)
print(f"Total changesets: {len(changesets)}")

api.close()
```

## Comparison with Similar Libraries

This implementation follows a pattern similar to:
- [swissparlpy](https://github.com/metaodi/swissparlpy) - Swiss Parliament OData API wrapper
- [sruthi](https://github.com/metaodi/sruthi) - SRU client with DataLoader pattern

The lazy loading approach provides a clean API while efficiently handling large result sets.
