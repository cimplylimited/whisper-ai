import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from utils.logger import get_logger

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive"
]

def get_service_account_credentials():
    key_path = os.getenv("SERVICE_ACCOUNT_FILE")
    if not key_path or not os.path.exists(key_path):
        logger.error("SERVICE_ACCOUNT_FILE environment variable not set or the file does not exist: %s", key_path)
        raise RuntimeError("SERVICE_ACCOUNT_FILE environment variable not set or the file does not exist.")
    try:
        creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
        # logger.info("Service account credentials loaded successfully.")  # Optional
        return creds
    except Exception as e:
        logger.error("Failed to load service account credentials: %s", str(e))
        raise

def get_gdoc_service(creds=None):
    """Returns googleapiclient docs client. If creds not passed, loads from SA file."""
    if creds is None:
        creds = get_service_account_credentials()
    try:
        return build("docs", "v1", credentials=creds, cache_discovery=False)
    except Exception as e:
        logger.error("Failed to build Google Docs API client: %s", str(e))
        raise

def get_drive_service(creds=None):
    """Returns googleapiclient drive client. If creds not passed, loads from SA file."""
    if creds is None:
        creds = get_service_account_credentials()
    try:
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        logger.error("Failed to build Google Drive API client: %s", str(e))
        raise

def get_docs_drive_clients():
    """Returns (docs_client, drive_client) tuple (for old compatibility)."""
    creds = get_service_account_credentials()
    try:
        docs_client = build("docs", "v1", credentials=creds, cache_discovery=False)
        drive_client = build("drive", "v3", credentials=creds, cache_discovery=False)
        return (docs_client, drive_client)
    except Exception as e:
        logger.error("Failed to build one or both Google API clients: %s", str(e))
        raise