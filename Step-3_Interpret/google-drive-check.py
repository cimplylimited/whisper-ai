from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaInMemoryUpload
import os, io, sys
# ------------------------------------------------------------------
# 0.  credentials + service
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = service_account.Credentials.from_service_account_file(
    os.environ["SERVICE_ACCOUNT_FILE"], scopes=SCOPES
)
drive = build("drive", "v3", credentials=creds)

# ------------------------------------------------------------------
PARENT_FOLDER = os.environ["OUTPUT_FOLDER_ID"]     # folder in a Shared Drive
FILE_NAME      = "sample.json"
FILE_CONTENT   = b'{"ping":"pong"}'
MIME_TYPE      = "application/json"

# ------------------------------------------------------------------
# 1. verify folder really exists & SA can see it
try:
    meta = drive.files().get(
        fileId=PARENT_FOLDER,
        fields="id, name, parents, driveId",
        supportsAllDrives=True,
    ).execute()
    print("Folder verified ->", meta)
except Exception as e:
    sys.exit(f"FATAL: parent folder id invalid or not visible: {e}")

# ------------------------------------------------------------------
# 2. create/upload a file *inside that folder*
file_metadata = {
    "name": FILE_NAME,
    "parents": [PARENT_FOLDER],   # <— this is the ONLY place the folder id is used
}
media = MediaInMemoryUpload(FILE_CONTENT, mimetype=MIME_TYPE, resumable=False)

try:
    created = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id",
        supportsAllDrives=True        # <-- REQUIRED for Shared Drive destinations
    ).execute()
    print("Created file id:", created["id"])
except Exception as e:
    sys.exit(f"Upload failed: {e}")