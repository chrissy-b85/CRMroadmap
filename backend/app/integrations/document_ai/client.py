"""Google Document AI Invoice Parser client."""
from __future__ import annotations

import asyncio
import os
from typing import Any

from app.integrations.document_ai.parser import InvoiceParseResult, parse_document_ai_response

DOCUMENT_AI_PROJECT_ID: str = os.getenv("DOCUMENT_AI_PROJECT_ID", "")
DOCUMENT_AI_LOCATION: str = os.getenv("DOCUMENT_AI_LOCATION", "us")
DOCUMENT_AI_PROCESSOR_ID: str = os.getenv("DOCUMENT_AI_PROCESSOR_ID", "")


class DocumentAIClient:
    """Async wrapper around the Google Document AI SDK."""

    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from google.cloud import documentai  # type: ignore[import]

            opts = {"api_endpoint": f"{DOCUMENT_AI_LOCATION}-documentai.googleapis.com"}
            self._client = documentai.DocumentProcessorServiceClient(
                client_options=opts  # type: ignore[arg-type]
            )
        return self._client

    def _processor_name(self) -> str:
        return (
            f"projects/{DOCUMENT_AI_PROJECT_ID}/locations/{DOCUMENT_AI_LOCATION}"
            f"/processors/{DOCUMENT_AI_PROCESSOR_ID}"
        )

    def _process_sync(self, pdf_bytes: bytes) -> dict:
        from google.cloud import documentai  # type: ignore[import]

        client = self._get_client()
        raw_document = documentai.RawDocument(content=pdf_bytes, mime_type="application/pdf")
        request = documentai.ProcessRequest(
            name=self._processor_name(), raw_document=raw_document
        )
        result = client.process_document(request=request)
        # Convert protobuf to dict via the SDK helper
        return documentai.Document.to_dict(result.document)

    async def parse_invoice(self, pdf_bytes: bytes) -> InvoiceParseResult:
        """Send *pdf_bytes* to Document AI and return a structured parse result."""
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, lambda: self._process_sync(pdf_bytes))
        return parse_document_ai_response({"document": raw})
