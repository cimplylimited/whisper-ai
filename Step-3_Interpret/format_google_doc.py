from dotenv import load_dotenv
import os
import io
import json
import csv
import datetime

# Load .env settings BEFORE any os.getenv loads.
load_dotenv()

# Debug environment variable print. Remove for production.
print("[DEBUG] SERVICE_ACCOUNT_FILE =", os.getenv("SERVICE_ACCOUNT_FILE"))
print("[DEBUG] SUMMARY_JSON_FOLDER_ID =", os.getenv("OUTPUT_FOLDER_ID"))
print("[DEBUG] DEST_DOCS_FOLDER_ID =", os.getenv("DEST_DOCS_FOLDER_ID"))
print("[DEBUG] REGISTRY_CSV_FILE_ID =", os.getenv("REGISTRY_CSV_FILE_ID"))

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SUMMARY_JSON_FOLDER_ID = os.getenv("OUTPUT_FOLDER_ID")  # The folder with JSON output summaries
DEST_DOCS_FOLDER_ID = os.getenv("DEST_DOCS_FOLDER_ID")
REGISTRY_CSV_FILE_ID = os.getenv("REGISTRY_CSV_FILE_ID")
PROCESS_NAME = "docsgen_v1"

required_env = [
    ("SERVICE_ACCOUNT_FILE", SERVICE_ACCOUNT_FILE),
    ("SUMMARY_JSON_FOLDER_ID", SUMMARY_JSON_FOLDER_ID),
    ("DEST_DOCS_FOLDER_ID", DEST_DOCS_FOLDER_ID),
    ("REGISTRY_CSV_FILE_ID", REGISTRY_CSV_FILE_ID)
]
missing = [k for k, v in required_env if not v]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}. Did you set these in your .env file or environment?")

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload

def authenticate():
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents'
    ]
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('docs', 'v1', credentials=creds), build('drive', 'v3', credentials=creds)

def get_drive_file_url(file_id):
    return f"https://drive.google.com/file/d/{file_id}/view"

# --- Robustly list all files, then filter for .json suffix in Python for case safety ---
def list_json_files(drive_service, folder_id):
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType, createdTime)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    all_files = results.get('files', [])
    print(f"[DEBUG] All files in folder ({len(all_files)}):")
    for f in all_files:
        print(f"    - {f['name']} ({f['id']}) [type: {f.get('mimeType')}]")
    only_jsons = [f for f in all_files if f['name'].lower().endswith('.json')]
    print(f"[DEBUG] Files ending with .json: {len(only_jsons)}")
    for f in only_jsons:
        print(f"    - {f['name']}")
    return only_jsons

def get_json_content(drive_service, file_id):

    # JSON summary download
    request = drive_service.files().get_media(
        fileId=file_id,
        supportsAllDrives=True        # <-- add
    )

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return json.loads(fh.read().decode('utf-8'))

def move_doc_to_folder(drive_service, doc_id, folder_id):
    
    # get parents before move
    file = drive_service.files().get(
        fileId=doc_id,
        fields='parents',
        supportsAllDrives=True        # <-- add
    ).execute()

    prev_parents = ",".join(file.get('parents', []))
    drive_service.files().update(
        fileId=doc_id,
        addParents=folder_id,
        removeParents=prev_parents,
        supportsAllDrives=True).execute()

def load_processed_ids_from_log(drive_service, log_file_id):
    try:
        # registry download
        request = drive_service.files().get_media(
            fileId=log_file_id,
            supportsAllDrives=True        # <-- add
        )

        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        csv_text = buf.read().decode('utf-8').splitlines()
        if not csv_text or not csv_text[0]:
            return set(), []
        reader = csv.DictReader(csv_text)
        ids = set()
        all_rows = []
        for row in reader:
            ids.add(row['json_file_id'])
            all_rows.append(row)
        return ids, all_rows
    except Exception as e:
        print(f"[DEBUG] Error loading registry (ok on first run): {str(e)}")
        return set(), []

def append_to_processing_log(drive_service, log_file_id, old_rows, new_rows, fieldnames):
    output_csv = io.StringIO()
    writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
    writer.writeheader()
    if old_rows:
        writer.writerows(old_rows)
    writer.writerows(new_rows)
    output_csv.seek(0)
    media = MediaInMemoryUpload(output_csv.read().encode('utf-8'), mimetype="text/csv")
    drive_service.files().update(fileId=log_file_id, media_body=media).execute()

def create_gdoc_from_json(doc_service, title, requests, dest_folder_id=None):
    doc = doc_service.documents().create(body={'title': title}).execute()
    doc_id = doc.get('documentId')
    
    # --- Diagnostic block: Show requests near the TOC and check for list-structure bugs
    print("\n[DEBUG] ---- Outbound requests around failing TOC ----")
    for i, req in enumerate(requests):
        if isinstance(req, list):
            print(f"[DEBUG] Nested list at requests[{i}]:", req)
    failing_range = range(245, min(250, len(requests)))
    for i in failing_range:
        print(f"[DEBUG] requests[{i}]: {requests[i]}")
    print(f"[DEBUG] Total requests: {len(requests)}\n")
    # Also print the structure of the failing TOC request
    import json
    try:
        print("[DEBUG] Failing block as JSON:\n", json.dumps(requests[245:250], indent=2))
    except Exception as e:
        print(f"[DEBUG] JSON dump failed: {e}")

    # --- batchUpdate as usual ---
    try:
        doc_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    except Exception as e:
        print("BatchUpdate failed:", e)
        raise
    # --- move doc to folder if specified ---
    if dest_folder_id:
        from googleapiclient.errors import HttpError
        try:
            move_doc_to_folder(doc_service._http.credentials.with_scopes_if_required(["https://www.googleapis.com/auth/drive"]), doc_id, dest_folder_id)
        except HttpError as e:
            print("Move to folder failed:", e)
    return doc_id

def generate_doc_body(summary,
                      transcript_url: str | None = None,
                      summary_url: str | None = None) -> list[dict]:
    """
    Builds a list of Google-Docs batchUpdate requests.
    Every insertText/insertTable is done at location.index == 1
    (i.e., “append at end so far”), then immediately styled.
    The list is reversed before it is returned so the document renders in
    top-down order for the reader.
    """

    requests: list[dict] = []          # we build BACK-TO-FRONT

    # ------------------------------------------------------------------ #
    # helpers                                                            #
    # ------------------------------------------------------------------ #
    def safe_str(obj) -> str:
        if isinstance(obj, str):
            return obj
        try:
            return json.dumps(obj, ensure_ascii=False)
        except Exception:
            return str(obj)

    def prepend_insert(text: str):
        """insert `text` (must include trailing \n if new paragraph)"""
        requests.append({"insertText": {"location": {"index": 1},
                                        "text": text}})

    def prepend_heading(text: str, level: int):
        """insert a heading paragraph"""
        txt = safe_str(text) + "\n"
        # Style request must come *after* the insert
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": 1,
                          "endIndex": 1 + len(txt)},
                "paragraphStyle": {"namedStyleType": f"HEADING_{level}"},
                "fields": "namedStyleType"
            }
        })
        prepend_insert(txt)

    def prepend_title(text: str):
        txt = safe_str(text) + "\n"
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": 1,
                          "endIndex": 1 + len(txt)},
                "paragraphStyle": {"namedStyleType": "TITLE"},
                "fields": "namedStyleType"
            }
        })
        prepend_insert(txt)

    def prepend_bullets(lines: list[str]):
        if not lines:
            return
        block = "\n".join(f"• {safe_str(l)}" for l in lines) + "\n\n"
        prepend_insert(block)

    def prepend_table(headers: list[str], rows: list[dict]):
        """
        Very safe table writer: create table, then write cell texts immediately;
        no style updates that reference ranges, so no risk of range errors.
        """
        if not rows:
            return
        n_rows = len(rows) + 1
        n_cols = len(headers)
        requests.append({"insertTable": {
            "rows": n_rows,
            "columns": n_cols,
            "location": {"index": 1}
        }})
        cell_idx = 1
        # header row
        for h in headers:
            prepend_insert(safe_str(h))
            cell_idx += len(safe_str(h))
        cell_idx += 1  # end of header row
        # data rows
        for row in rows:
            for h in headers:
                prepend_insert(safe_str(row.get(h, "")))
                cell_idx += len(safe_str(row.get(h, "")))
            cell_idx += 1  # end row
        cell_idx += 1

    # ------------------------------------------------------------------ #
    #  Build BACK-TO-FRONT (last section first)                          #
    # ------------------------------------------------------------------ #

    # Links & References -------------------------------------------------
    refs = []
    if transcript_url:
        refs.append("• Original Transcript: " + transcript_url)
    if summary_url:
        refs.append("• Structured JSON: " + summary_url)
    if refs:
        prepend_bullets(refs)
        prepend_heading("Links & References", 2)

    # Tabular sections ---------------------------------------------------
    for key, lbl in [
        ("james_grant_actions",  "James Grant Actions"),
        ("executive_followup",   "Executive Follow-up"),
        ("strategic_initiatives","Strategic Initiatives"),
        ("next_steps",           "Next Steps")
    ]:
        rows = summary.get(key, [])
        if rows:
            headers = list(rows[0].keys())
            prepend_table(headers, rows)
            prepend_heading(lbl, 1)

    # Key blocks ---------------------------------------------------------
    if summary.get("key_takeaways"):
        prepend_bullets(summary["key_takeaways"])
        prepend_heading("Key Takeaways", 1)

    if summary.get("outline"):
        prepend_bullets(summary["outline"])
        prepend_heading("Outline", 1)

    if summary.get("summary"):
        prepend_insert(safe_str(summary["summary"]) + "\n\n")
        prepend_heading("Executive Summary", 1)

    # Meta ---------------------------------------------------------------
    meta_lines = [
        f"Date: {safe_str(summary.get('date', ''))}",
        f"Attendees: {safe_str(', '.join(summary.get('attendees', [])))}"
    ]
    if transcript_url:
        meta_lines.append(f"Original Transcript: {transcript_url}")
    if summary_url:
        meta_lines.append(f"Structured JSON: {summary_url}")
    prepend_insert("\n".join(meta_lines) + "\n\n")

    # Dummy 'Contents' heading (helps Outline) ---------------------------
    prepend_heading("Contents", 1)

    # Title (will appear first after we reverse) -------------------------
    prepend_title(summary.get("title", "[No Title]"))

    # ------------------------------------------------------------------ #
    # All done – reverse to top-down order and return                     #
    # ------------------------------------------------------------------ #
    return list(reversed(requests))

def main():
    print("Authenticating...")
    doc_service, drive_service = authenticate()

    # diagnostic fetch
    meta = drive_service.files().get(
        fileId=REGISTRY_CSV_FILE_ID,
        fields="id, name, mimeType",
        supportsAllDrives=True        # <-- add
    ).execute()
    
    print("[DEBUG] Registry file metadata:", meta)
    
    print("Loading registry...")
    processed_ids, registry_rows = load_processed_ids_from_log(drive_service, REGISTRY_CSV_FILE_ID)

    print(f"[DEBUG] Listing incoming JSON summaries in folder {SUMMARY_JSON_FOLDER_ID}...")
    json_files = list_json_files(drive_service, SUMMARY_JSON_FOLDER_ID)
    to_process = [f for f in json_files if f['id'] not in processed_ids]
    print(f"{len(json_files)} total found; {len(to_process)} needing processing.")

    registry_fieldnames = [
        "json_file_id", "json_file_name", "transcript_file_id", "output_doc_id", "output_doc_name",
        "output_doc_url", "processed_by", "timestamp", "status", "error"
    ]
    entries_to_log = []

    for entry in to_process:
        file_id, file_name = entry['id'], entry['name']
        print(f"Processing: {file_name}...")
        try:
            summary = get_json_content(drive_service, file_id)
            transcript_id = summary.get("transcript_file_id", "")
            transcript_url = get_drive_file_url(transcript_id) if transcript_id else ""
            summary_url = get_drive_file_url(file_id)
            title = summary.get('title', f"Meeting_Notes_{file_id[:6]}")
            doc_requests = generate_doc_body(summary, transcript_url=transcript_url, summary_url=summary_url)
            doc_id = create_gdoc_from_json(doc_service, title, doc_requests)
            move_doc_to_folder(drive_service, doc_id, DEST_DOCS_FOLDER_ID)
            doc_url = get_drive_file_url(doc_id)
            print(f"  Done. Google Doc: {doc_url}")

            entries_to_log.append({
                "json_file_id": file_id,
                "json_file_name": file_name,
                "transcript_file_id": transcript_id,
                "output_doc_id": doc_id,
                "output_doc_name": title,
                "output_doc_url": doc_url,
                "processed_by": PROCESS_NAME,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "status": "success",
                "error": ""
            })
        except Exception as e:
            print(f"  FAILED: {str(e)}")
            entries_to_log.append({
                "json_file_id": file_id,
                "json_file_name": file_name,
                "transcript_file_id": "",
                "output_doc_id": "",
                "output_doc_name": "",
                "output_doc_url": "",
                "processed_by": PROCESS_NAME,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            })

    if entries_to_log:
        append_to_processing_log(
            drive_service,
            REGISTRY_CSV_FILE_ID,
            registry_rows,
            entries_to_log,
            registry_fieldnames
        )
        print(f"Updated processing registry with {len(entries_to_log)} new rows.")

    print("All done.")

if __name__ == "__main__":
    main()

