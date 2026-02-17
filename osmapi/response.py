"""
Response classes for lazy loading API results.
"""

import logging
from typing import Iterator, Union, Optional, Callable
from . import dom

logger = logging.getLogger(__name__)


class ChangesetsResponse:
    """
    A lazy loading response object for changesets.

    This class allows iterating over changesets and accessing them by index
    without loading all data upfront. It automatically fetches more data
    from the API as needed.

    The response object behaves like a dict with changeset IDs as keys,
    maintaining backward compatibility with the previous API.
    """

    def __init__(
        self,
        session,
        uri_builder: Callable[[Optional[str]], str],
        params: dict,
    ):
        """
        Initialize the ChangesetsResponse.

        Args:
            session: The OsmApiSession instance for making API calls
            uri_builder: Function that builds the URI for the next request,
                        takes the last changeset timestamp as argument
            params: Initial query parameters
        """
        self.session = session
        self.uri_builder = uri_builder
        self.params = params
        self.data: dict = {}  # {changeset_id: changeset_data}
        self.next_timestamp: Optional[str] = None
        self.has_more = True
        self._loaded_initial = False

        # Load the first batch immediately (eager loading of first page)
        self._load_batch()
        self._loaded_initial = True

    def _load_batch(self) -> None:
        """Load the next batch of changesets from the API."""
        if not self.has_more:
            return

        uri = self.uri_builder(self.next_timestamp)
        logger.debug(f"Loading batch from URI: {uri}")

        response_data = self.session._get(uri)
        changesets = dom.OsmResponseToDom(response_data, tag="changeset")

        if not changesets:
            self.has_more = False
            return

        batch_count = 0
        latest_timestamp = None

        for changeset_elem in changesets:
            parsed = dom.DomParseChangeset(changeset_elem)
            changeset_id = parsed["id"]

            if changeset_id not in self.data:
                self.data[changeset_id] = parsed
                batch_count += 1

                # Track the latest timestamp for pagination
                created_at = parsed.get("created_at")
                if created_at and (latest_timestamp is None or created_at > latest_timestamp):
                    latest_timestamp = created_at

        logger.debug(f"Loaded {batch_count} new changesets (total: {len(self.data)})")

        # If we got fewer than 100 changesets (typical API limit), we've reached the end
        if len(changesets) < 100:
            self.has_more = False
        else:
            # Use the latest timestamp for the next request
            if latest_timestamp:
                self.next_timestamp = latest_timestamp.isoformat()
            else:
                self.has_more = False

    def _ensure_loaded(self) -> None:
        """Ensure at least the initial batch is loaded."""
        if not self._loaded_initial:
            self._load_batch()
            self._loaded_initial = True

    def load_all(self) -> None:
        """Load all available changesets from the API."""
        self._ensure_loaded()
        while self.has_more:
            self._load_batch()

    def __len__(self) -> int:
        """Return the current number of loaded changesets."""
        self._ensure_loaded()
        return len(self.data)

    def __iter__(self) -> Iterator[int]:
        """Iterate over changeset IDs, loading more data as needed."""
        self._ensure_loaded()

        # Yield currently loaded IDs
        yielded_ids = set()
        for changeset_id in self.data:
            yielded_ids.add(changeset_id)
            yield changeset_id

        # Load and yield additional batches
        while self.has_more:
            old_count = len(self.data)
            self._load_batch()

            # Yield newly loaded IDs
            for changeset_id in self.data:
                if changeset_id not in yielded_ids:
                    yielded_ids.add(changeset_id)
                    yield changeset_id

            # Safety check: if no new data was loaded, break
            if len(self.data) == old_count:
                break

    def __getitem__(self, key: int) -> dict:
        """
        Get a changeset by ID.

        Args:
            key: The changeset ID

        Returns:
            The changeset data dict

        Raises:
            KeyError: If the changeset ID is not found after loading all data
        """
        self._ensure_loaded()

        # If not in current data and more data is available, try loading more
        if key not in self.data and self.has_more:
            self.load_all()

        return self.data[key]

    def __contains__(self, key: int) -> bool:
        """Check if a changeset ID exists."""
        self._ensure_loaded()

        # If not in current data and more data is available, try loading more
        if key not in self.data and self.has_more:
            self.load_all()

        return key in self.data

    def keys(self):
        """Return changeset IDs (loads all data)."""
        self.load_all()
        return self.data.keys()

    def values(self):
        """Return changeset data (loads all data)."""
        self.load_all()
        return self.data.values()

    def items(self):
        """Return changeset ID-data pairs (loads all data)."""
        self.load_all()
        return self.data.items()

    def get(self, key: int, default=None):
        """Get a changeset by ID, returning default if not found."""
        try:
            return self[key]
        except KeyError:
            return default

    def as_dict(self) -> dict:
        """
        Return all changesets as a regular dict.
        This loads all data from the API.
        """
        self.load_all()
        return dict(self.data)
