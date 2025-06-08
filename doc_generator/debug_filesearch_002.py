import os
from dotenv import load_dotenv
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from utils.logger import get_logger

logger = get_logger("auth_debug")

# Load .env and env variables
ENV_PATH = os.getenv("DOCGEN_ENV_PATH", ".env")
load_dotenv(dotenv_path=Path(ENV_PATH))

DOC_ID = os.getenv("DOCGEN_TEMPLATE_DOC_ID")
SA_PATH = os.getenv("SERVICE_ACCOUNT_FILE")

if not DOC_ID or not SA_PATH:
    logger.error("Missing DOCGEN_TEMPLATE_DOC_ID or SERVICE_ACCOUNT_FILE in .env!")
    print("ERROR: Missing DOCGEN_TEMPLATE_DOC_ID or SERVICE_ACCOUNT_FILE in .env!")
    exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents"
]

# Step 1: Authenticate service account
try:
    creds = Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
    logger.info("Service account authentication successful as: %s", creds.service_account_email)
    print(f"AUTH SUCCESS: Service account authenticated as: {creds.service_account_email}\n")
except Exception as e:
    logger.error("Service account authentication failed: %s", str(e))
    print("AUTH ERROR: Service account authentication failed. See log for details.\n")
    exit(1)

# Step 2: Check template doc access
drive = build("drive", "v3", credentials=creds)

try:
    metadata = drive.files().get(fileId=DOC_ID, supportsAllDrives=True).execute()
    logger.info("Service account has access to template doc ID: %s", DOC_ID)
    print("SUCCESS: Service account CAN access the template file!")
    print("-" * 60)
    print("File Metadata:")
    for k, v in metadata.items():
        print(f"{k:20}: {v}")
    print("-" * 60)
except Exception as e:
    logger.error("Service account CANNOT access template file (ID: %s): %s", DOC_ID, str(e))
    print("ERROR: Service account CANNOT access the template file.\n")
    print(f"File ID: {DOC_ID}")
    print(f"Service Account: {creds.service_account_email}")
    print(e)
    print("\nHave you shared the document with the service account email above as an Editor?")
    exit(1)