import os


def get_ocr_client():
    """Return the configured OCR client.

    Set OCR_BACKEND=textract to use Amazon Textract.
    Defaults to 'documentai' (Google Document AI).
    """
    backend = os.getenv("OCR_BACKEND", "documentai")
    if backend == "textract":
        from app.integrations.textract.client import TextractClient
        return TextractClient()
    from app.integrations.document_ai.client import DocumentAIClient
    return DocumentAIClient()
