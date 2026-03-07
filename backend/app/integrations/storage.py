"""Storage backend factory.

Set the ``STORAGE_BACKEND`` environment variable to choose the backend:

- ``gcs`` (default) — Google Cloud Storage via :class:`~app.integrations.gcs.client.GCSClient`
- ``spaces`` — DigitalOcean Spaces via :class:`~app.integrations.spaces.client.SpacesClient`
"""

from __future__ import annotations

import os


def get_storage_client():
    """Return the configured storage client instance."""
    backend = os.getenv("STORAGE_BACKEND", "gcs")
    if backend == "spaces":
        from app.integrations.spaces.client import SpacesClient

        return SpacesClient()
    from app.integrations.gcs.client import GCSClient

    return GCSClient()
