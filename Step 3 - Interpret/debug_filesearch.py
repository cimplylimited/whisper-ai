import os
import ast
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account

def authenticate_google_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def main():
    load_dotenv()

    try:
        RECORDING_FOLDER_IDS = ast.literal_eval(os.getenv("RECORDING_FOLDER_IDS", "[]"))
    except Exception as e:
        print("Error parsing RECORDING_FOLDER_IDS from env:", e)
        return

    service = authenticate_google_drive()

    for folder_id in RECORDING_FOLDER_IDS:
        print(f"\n--- Listing ALL (non-trashed) files in folder: {folder_id} ---")
        page_token = None
        while True:
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, name, mimeType, owners, permissions)",
                supportsAllDrives=True,
                pageSize=1000,
                pageToken=page_token
            ).execute()
            for f in results.get('files', []):
                owners = ','.join([o['emailAddress'] for o in f.get('owners', [])])
                perms = ','.join([p.get('role','')+':'+p.get('emailAddress','') for p in f.get('permissions',[])])
                print(f"{f['id']} | {f['name']} | {f['mimeType']} | owners: {owners} | perms: {perms}")
            page_token = results.get('nextPageToken', None)
            if not page_token:
                break

if __name__ == "__main__":
    main()