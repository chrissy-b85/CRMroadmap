"""Microsoft Graph API configuration from environment variables."""
import os

GRAPH_TENANT_ID: str = os.getenv("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID: str = os.getenv("GRAPH_CLIENT_ID", "")
GRAPH_CLIENT_SECRET: str = os.getenv("GRAPH_CLIENT_SECRET", "")
GRAPH_SHARED_MAILBOX: str = os.getenv("GRAPH_SHARED_MAILBOX", "")
GRAPH_PROCESSED_FOLDER_ID: str = os.getenv("GRAPH_PROCESSED_FOLDER_ID", "")
GRAPH_CORRESPONDENCE_FOLDER_ID: str = os.getenv("GRAPH_CORRESPONDENCE_FOLDER_ID", "")
GRAPH_FROM_MAILBOX: str = os.getenv("GRAPH_FROM_MAILBOX", os.getenv("GRAPH_SHARED_MAILBOX", ""))
