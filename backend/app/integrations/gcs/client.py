"""GCS client for invoice PDF and JSON storage."""

from __future__ import annotations

import asyncio
import datetime
import io
import json
import os
from typing import Any

GCS_BUCKET_INVOICES: str = os.getenv("GCS_BUCKET_INVOICES", "ndis-crm-invoices")


class GCSClient:
    """Async wrapper around the google-cloud-storage SDK."""

    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from google.cloud import storage  # type: ignore[import]

            self._client = storage.Client()
        return self._client

    def _bucket(self) -> Any:
        return self._get_client().bucket(GCS_BUCKET_INVOICES)

    # ------------------------------------------------------------------
    # Public async methods
    # ------------------------------------------------------------------

    async def upload_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        participant_id: str | None,
    ) -> str:
        """Upload a PDF to GCS and return its ``gs://`` URI."""
        prefix = f"participants/{participant_id}" if participant_id else "unmatched"
        blob_name = f"invoices/{prefix}/{filename}"

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self._upload_blob(blob_name, pdf_bytes, "application/pdf")
        )
        return f"gs://{GCS_BUCKET_INVOICES}/{blob_name}"

    async def upload_json(self, data: dict, filename: str) -> str:
        """Upload a JSON dict to GCS and return its ``gs://`` URI."""
        blob_name = f"invoices/ocr/{filename}"
        raw = json.dumps(data, default=str).encode()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self._upload_blob(blob_name, raw, "application/json")
        )
        return f"gs://{GCS_BUCKET_INVOICES}/{blob_name}"

    async def get_signed_url(self, gcs_path: str, expiry_minutes: int = 60) -> str:
        """Generate a signed URL for temporary access to a GCS object.

        ``gcs_path`` should be a ``gs://bucket/blob`` URI.
        The path must refer to an object within the configured invoices bucket.
        """
        if gcs_path.startswith("gs://"):
            parts = gcs_path[5:].split("/", 1)
            bucket_name, blob_name = parts[0], parts[1] if len(parts) > 1 else ""
        else:
            blob_name = gcs_path
            bucket_name = GCS_BUCKET_INVOICES

        if bucket_name != GCS_BUCKET_INVOICES:
            raise ValueError(
                f"Signed URL generation is only allowed for bucket '{GCS_BUCKET_INVOICES}'"
            )

        expiry = datetime.timedelta(minutes=expiry_minutes)
        client = self._get_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        loop = asyncio.get_event_loop()
        url: str = await loop.run_in_executor(
            None,
            lambda: blob.generate_signed_url(expiration=expiry, method="GET"),
        )
        return url

    async def upload_bytes(
        self,
        data: bytes,
        blob_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        """Upload raw bytes to an explicit blob path and return its ``gs://`` URI."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self._upload_blob(blob_path, data, content_type)
        )
        return f"gs://{GCS_BUCKET_INVOICES}/{blob_path}"

    # ------------------------------------------------------------------
    # Internal sync helper
    # ------------------------------------------------------------------

    def _upload_blob(self, blob_name: str, data: bytes, content_type: str) -> None:
        bucket = self._bucket()
        blob = bucket.blob(blob_name)
        blob.upload_from_file(io.BytesIO(data), content_type=content_type)
