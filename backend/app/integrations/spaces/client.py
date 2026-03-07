"""DigitalOcean Spaces client for invoice PDF and JSON storage."""

from __future__ import annotations

import asyncio
import io
import json
import os
from typing import Any

DO_SPACES_KEY: str = os.getenv("DO_SPACES_KEY", "")
DO_SPACES_SECRET: str = os.getenv("DO_SPACES_SECRET", "")
DO_SPACES_REGION: str = os.getenv("DO_SPACES_REGION", "syd1")
DO_SPACES_BUCKET: str = os.getenv("DO_SPACES_BUCKET", "ndis-crm-files")
DO_SPACES_ENDPOINT: str = os.getenv(
    "DO_SPACES_ENDPOINT", "https://syd1.digitaloceanspaces.com"
)


class SpacesClient:
    """Async wrapper around boto3 (S3-compatible) for DigitalOcean Spaces.

    Implements the same public interface as :class:`~app.integrations.gcs.client.GCSClient`
    so callers can swap backends by changing ``STORAGE_BACKEND``.
    """

    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import boto3  # type: ignore[import]

            self._client = boto3.client(
                "s3",
                region_name=DO_SPACES_REGION,
                endpoint_url=DO_SPACES_ENDPOINT,
                aws_access_key_id=DO_SPACES_KEY,
                aws_secret_access_key=DO_SPACES_SECRET,
            )
        return self._client

    # ------------------------------------------------------------------
    # Public async methods
    # ------------------------------------------------------------------

    async def upload_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        participant_id: str | None,
    ) -> str:
        """Upload a PDF to Spaces and return its ``s3://`` URI."""
        prefix = f"participants/{participant_id}" if participant_id else "unmatched"
        key = f"invoices/{prefix}/{filename}"

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self._upload_object(key, pdf_bytes, "application/pdf")
        )
        return f"s3://{DO_SPACES_BUCKET}/{key}"

    async def upload_json(self, data: dict, filename: str) -> str:
        """Upload a JSON dict to Spaces and return its ``s3://`` URI."""
        key = f"invoices/ocr/{filename}"
        raw = json.dumps(data, default=str).encode()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self._upload_object(key, raw, "application/json")
        )
        return f"s3://{DO_SPACES_BUCKET}/{key}"

    async def get_signed_url(self, path: str, expiry_minutes: int = 60) -> str:
        """Generate a presigned URL for temporary access to a Spaces object.

        ``path`` may be either a ``s3://bucket/key`` URI or a plain key.
        """
        if path.startswith("s3://"):
            parts = path[5:].split("/", 1)
            bucket_name = parts[0]
            key = parts[1] if len(parts) > 1 else ""
        else:
            bucket_name = DO_SPACES_BUCKET
            key = path

        client = self._get_client()
        loop = asyncio.get_event_loop()
        url: str = await loop.run_in_executor(
            None,
            lambda: client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": key},
                ExpiresIn=expiry_minutes * 60,
            ),
        )
        return url

    async def upload_bytes(
        self,
        data: bytes,
        blob_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        """Upload raw bytes to an explicit key path and return its ``s3://`` URI."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self._upload_object(blob_path, data, content_type)
        )
        return f"s3://{DO_SPACES_BUCKET}/{blob_path}"

    # ------------------------------------------------------------------
    # Internal sync helper
    # ------------------------------------------------------------------

    def _upload_object(self, key: str, data: bytes, content_type: str) -> None:
        client = self._get_client()
        client.put_object(
            Bucket=DO_SPACES_BUCKET,
            Key=key,
            Body=io.BytesIO(data),
            ContentType=content_type,
            ACL="private",
        )
