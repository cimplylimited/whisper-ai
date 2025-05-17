import os
import ast
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/drive"]

def check_id(service, fid, label):
    print(f"\n--- {label} ({fid}) ---")
    try:
        meta = service.files().get(
            fileId=fid,
            fields="id, name, mimeType, trashed, parents, driveId, webViewLink, permissions"
        ).execute()
        print(f"  Name: {meta.get('name', '???')}")
        print(f"  Type: {meta.get('mimeType','???')}")
        print(f"  Trashed: {meta.get('trashed', False)}")
        print(f"  WebLink: {meta.get('webViewLink')}")
        print(f"  Drive ID: {meta.get('driveId')}")
        print(f"  Parent(s): {meta.get('parents')}")
        perms = meta.get("permissions", [])
        print(f"  Permissions ({len(perms)}): {[p.get('role','')+':'+p.get('emailAddress','') for p in perms]}")
        if meta['mimeType'] == 'application/vnd.google-apps.folder':
            print("  Listing up to 3 children (if any):")
            files = service.files().list(
                q=f"'{fid}' in parents and trashed=false",
                pageSize=3, fields="files(id, name)", supportsAllDrives=True
            ).execute().get("files", [])
            if files:
                for f in files:
                    print(f"    - {f['id']}: {f['name']}")
            else:
                print("    (No visible files or empty folder)")
    except HttpError as e:
        if e.resp.status == 403:
            print("  [403 Forbidden! Your service account does not have access.]")
        elif e.resp.status == 404:
            print("  [404 Not Found! Wrong ID, deleted, or outside drive scope.]")
        else:
            print(f"  [HttpError {e.resp.status}]: {e}")
    except Exception as e:
        print("  [ERROR]:", e)

def main():
    load_dotenv()
    cred = os.getenv("SERVICE_ACCOUNT_FILE")
    if not cred or not os.path.exists(cred):
        print(f"SERVICE_ACCOUNT_FILE is missing: {cred}")
        return

    creds = service_account.Credentials.from_service_account_file(
        cred, scopes=SCOPES)
    svc = build('drive', 'v3', credentials=creds)

    print("Testing Google Drive access using:")
    print("  SERVICE_ACCOUNT_FILE:", cred)
    print("  RECORDING_FOLDER_IDS:", os.getenv("RECORDING_FOLDER_IDS"))
    print("  PROCESSED_FOLDER_ID:", os.getenv("PROCESSED_FOLDER_ID"))
    print("  OUTPUT_FOLDER_ID:", os.getenv("OUTPUT_FOLDER_ID"))

    try:
        print("\nListing up to 5 Shared Drives:")
        drives = svc.drives().list(pageSize=5).execute()
        for d in drives.get("drives", []):
            print("   -", d["id"], "::", d["name"])
    except Exception as e:
        print("  [Could not list shared drives - maybe not permitted?]", e)

    # Check recording folders
    try:
        recs = ast.literal_eval(os.getenv("RECORDING_FOLDER_IDS", "[]"))
        for i, fid in enumerate(recs):
            check_id(svc, fid, f"RECORDING_FOLDER_{i+1}")
    except Exception as e:
        print("  RECORDING_FOLDER_IDS error:", e)

    # Check processed and output folders
    pid = os.getenv("PROCESSED_FOLDER_ID")
    if pid: check_id(svc, pid, "PROCESSED_FOLDER")
    oid = os.getenv("OUTPUT_FOLDER_ID")
    if oid: check_id(svc, oid, "OUTPUT_FOLDER")

    print("\nDone.")

if __name__ == "__main__":
    main()