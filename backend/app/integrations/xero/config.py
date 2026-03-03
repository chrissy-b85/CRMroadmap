"""Xero integration configuration loaded from environment variables."""
import os

XERO_CLIENT_ID: str = os.getenv("XERO_CLIENT_ID", "")
XERO_CLIENT_SECRET: str = os.getenv("XERO_CLIENT_SECRET", "")
XERO_REDIRECT_URI: str = os.getenv(
    "XERO_REDIRECT_URI", "http://localhost:8000/xero/callback"
)
XERO_WEBHOOK_KEY: str = os.getenv("XERO_WEBHOOK_KEY", "")
