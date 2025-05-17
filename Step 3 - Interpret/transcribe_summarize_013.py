import os
import json
import re
import io
import time
import logging
import ast
import datetime
import csv
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================
# Logging Configuration
# ==========================
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('script.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ==========================
# Load Config from .env (or env)
# ==========================
load_dotenv()
RECORDING_FOLDER_IDS = ast.literal_eval(os.getenv("RECORDING_FOLDER_IDS", "[]"))
PROCESSED_FOLDER_ID = os.getenv("PROCESSED_FOLDER_ID")
OUTPUT_FOLDER_ID = os.getenv("OUTPUT_FOLDER_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-2025-04-14")

# ==========================
# OpenAI Client
# ==========================
client = OpenAI(api_key=OPENAI_API_KEY)

# ... Place your SUMMARY_INSTRUCTIONS as a long string here ...

SUMMARY_INSTRUCTIONS ="""
Your name is James Grant.  You are a highly meticulous, detail-oriented meeting analyst. Your task is to review the following meeting transcript and produce a comprehensive, structured summary in JSON format for executive and operational use.

**Instructions:**
1. **Extraction (Do not summarize yet):**
   - Carefully read the entire transcript.
   - Identify **every key point, decision, action item, open question, and any notable comment—no matter how minor.**
   - **Do not attribute each point to a specific speaker** in your summary bullets, unless the identity is essential for understanding the point.
   - For each bullet, focus on the content, detail, and context **not who said it.**
   - **Do not omit any information** that could be relevant to any attendee or future planning.
2. **Task and Ownership Assignment:**
   - **Pay attention to who assigns tasks, who volunteers, or is delegated action items.**
   - When creating the `next_steps` section, use the transcript’s speaker information to assign owners to each task as accurately as possible.
   - Consider the relative priority and relative urgency of each assigned task on a scale of 1-10
3. **Categorization:**
   - Group extracted points into logical sections (e.g., topics, agenda items).
   - Tag any item that is especially important, controversial, or actionable.
4. **Detailed Summarization:**
   - For each group/section, write a detailed summary using **granular, content-rich bullet points**.
   - **Do not generalize** or omit specifics—be as detailed as possible.
   - **Do not include speaker names in summary bullets** unless essential for context.
5. **Structured Output:**
   - Populate the required JSON structure:
     - title, date, attendees, summary, outline (with detailed bullet points), key_takeaways, next_steps (with all required fields), strategic_initiatives, james_grant_items.
   - For all array fields (like outline, key_takeaways), use **detailed, granular bullet points**.
   - For `next_steps`, ensure each task is specific and assigns an owner, based on who was given or accepted the task in the transcript.
   - It is critical the template is followed for consistency in data parsing
6. **Special Emphasis:**
   - **Pay extra attention** to anything related to "James Grant" and ensure all such items are included in the `james_grant_items` section.
   - You are James Grant and these tasks require a separate thought process
     - They signal that as our assistant it is important to both partners to find these items and consider them in the context they were spoken
     - This will often relate to other parts of the business and may require some inference to determine where they should be reclassed and added for later discussion
   - Flag any ambiguous or unclear points for follow-up.  If something appears important but you do not understand we want you to tell us.
7. **Self-Check:**
   - Before producing the final output, **review your extracted points and summaries** to ensure nothing from the transcript is omitted or oversimplified.
   - Proof read and insert citations so we can attribute later.
8. **Output:**
   - Output only valid JSON as per the specified format, with all strings in double quotes and newlines as `\n`.

9. For the `next_steps`, `strategic_initiatives`, and `executive_followup` fields, each must be an array of objects. Each object must use the following fields only, in this exact order and with these names:
- description
- owner
- due_date
- urgency_score
- priority_score
- citation
- high_level_topic

Apply this format for all items in all three sections, with no field additions or omissions. 

10. After the "executive_followup" section, create a new field called "james_grant_actions". 
This must be an array of objects. 
Each object must contain the following fields, exactly as listed, in this order: 
- description
- owner
- due_date
- urgency_score
- priority_score
- citation
- high_level_topic
- james_grant_reference

For each actionable item, set `james_grant_reference` to true if "James Grant" is mentioned or assigned within the transcript for that item, otherwise false.
If there are no references to "James Grant" in the transcript, set "james_grant_actions" to an empty array.

This section must use the identical structure as the other actionable arrays but with the added james_grant_reference Boolean flag.

**Remember:**  
Your goal is to **leave no detail behind**, capture every nuance, and provide a summary that allows the team to reconstruct the full meeting context if needed, **without attributing each bullet to a specific person.**

Here is the required JSON format:

"next_steps": [
  {
    "description": "Brief actionable step",
    "owner": "Person/Role",
    "due_date": "YYYY-MM-DD",
    "urgency_score": "1-10",
    "priority_score": "1-10",
    "citation": "Para X or context",
    "high_level_topic": "Category"
  }
],
"strategic_initiatives": [
  {
    "description": "Brief description of initiative",
    "owner": "Person/Role",
    "due_date": "YYYY-MM-DD",
    "urgency_score": "1-10",
    "priority_score": "1-10",
    "citation": "Para X or context",
    "high_level_topic": "Category"
  }
],
"executive_followup": [
  {
    "description": "Executive follow-up item",
    "owner": "Person/Role",
    "due_date": "YYYY-MM-DD",
    "urgency_score": "1-10",
    "priority_score": "1-10",
    "citation": "Para X or context",
    "high_level_topic": "Category"
  }
],

"james_grant_actions": [
    {
      "description": "Review and approve the partner proposals.",
      "owner": "James Grant",
      "due_date": "2025-06-22",
      "urgency_score": "9",
      "priority_score": "10",
      "citation": "Para21",
      "high_level_topic": "Partnerships",
      "james_grant_reference": true
    }
]

  
"""


def log_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Starting '{func.__name__}'")
        start = time.time()
        result = func(*args, **kwargs)
        logger.debug(f"Completed '{func.__name__}' in {time.time()-start:.2f}s")
        return result
    return wrapper

def sanitize_filename(value):
    value = re.sub(r'[^\w\s-]', '', value)
    value = re.sub(r'[\s-]+', '_', value)
    return value.strip()[:80]

@log_execution_time
def authenticate_google_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

@log_execution_time
def list_google_docs_files(service, folder_id):
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.document' and trashed = false",
        pageSize=1000, fields="files(id, name)", supportsAllDrives=True
    ).execute()
    return results.get('files', [])

@log_execution_time
def get_file_content_from_google_drive(service, file_id):
    file = service.files().get(fileId=file_id, fields='mimeType, name').execute()
    if file.get('mimeType') == 'application/vnd.google-apps.document':
        request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        content = fh.read().decode('utf-8')
        fh.close()
        return content
    logger.warning(f"Unsupported file type {file.get('mimeType')} for file {file.get('name')}")
    return None

@log_execution_time
def upload_content_to_google_drive(service, content, filename, folder_id):
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaInMemoryUpload(content.encode("utf-8"), mimetype="application/json")
    service.files().create(
        body=file_metadata, media_body=media, fields='id', supportsAllDrives=True
    ).execute()

@log_execution_time
def copy_file_to_folder(service, file_id, dest_folder_id, new_name=None):
    body = {'parents': [dest_folder_id]}
    if new_name:
        body['name'] = new_name
    copied = service.files().copy(
        fileId=file_id, body=body, supportsAllDrives=True, fields='id,name'
    ).execute()
    return copied.get('id')

# === ARCHIVAL AND LOGIC HELPERS ===
def ensure_archive_folder(service, parent_folder_id):
    query = f"'{parent_folder_id}' in parents and name = 'transcript_archive' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, supportsAllDrives=True, fields="files(id, name)", pageSize=1).execute()
    files = results.get("files", [])
    if files:
        return files[0]['id']
    meta = {
        'name': 'transcript_archive',
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    folder = service.files().create(body=meta, fields='id', supportsAllDrives=True).execute()
    return folder['id']

def create_timestamped_processed_folder(service, archive_id):
    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    name = f"processed-transcripts_{now}"
    meta = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [archive_id]
    }
    folder = service.files().create(body=meta, fields='id', supportsAllDrives=True).execute()
    return folder['id'], name

def move_files_to_folder(service, file_ids, new_parent_id):
    for fid in file_ids:
        file = service.files().get(fileId=fid, fields='parents').execute()
        prev_parents = ",".join(file.get('parents', []))
        service.files().update(
            fileId=fid,
            addParents=new_parent_id,
            removeParents=prev_parents,
            fields='id, parents',
            supportsAllDrives=True
        ).execute()

def ensure_logs_folder(service, processed_folder_id):
    query = f"'{processed_folder_id}' in parents and name = 'logs' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, supportsAllDrives=True, fields="files(id, name)", pageSize=1).execute()
    files = results.get("files", [])
    if files:
        return files[0]['id']
    meta = {
        'name': 'logs',
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [processed_folder_id]
    }
    folder = service.files().create(body=meta, fields='id', supportsAllDrives=True).execute()
    return folder['id']

def append_to_csv_log(service, logs_folder_id, entries, archive_batch_id, user_folder_id):
    log_filename = "file_move_log.csv"
    query = f"'{logs_folder_id}' in parents and name = '{log_filename}' and trashed = false"
    results = service.files().list(q=query, supportsAllDrives=True, fields="files(id, name)", pageSize=1).execute()
    log_file = results.get("files", [])
    fieldnames = ["original_file_id", "file_name", "archive_batch_id", "date_moved", "user_folder_id"]
    now = datetime.datetime.now().isoformat()
    new_lines = [
        {
            "original_file_id": ent['file_id'],
            "file_name": ent['file_name'],
            "archive_batch_id": archive_batch_id,
            "date_moved": now,
            "user_folder_id": user_folder_id
        }
        for ent in entries
    ]
    if log_file:
        log_file_id = log_file[0]['id']
        request = service.files().get_media(fileId=log_file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buf.seek(0)
        csv_text = buf.read().decode('utf-8')
        output_lines = []
        reader = csv.DictReader(csv_text.splitlines())
        output_lines.extend(list(reader))
        output_lines.extend(new_lines)
        output_buf = io.StringIO()
        writer = csv.DictWriter(output_buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_lines)
        output_buf.seek(0)
        media = MediaInMemoryUpload(output_buf.read().encode('utf-8'), mimetype="text/csv")
        service.files().update(
            fileId=log_file_id,
            media_body=media,
            fields='id'
        ).execute()
    else:
        output_buf = io.StringIO()
        writer = csv.DictWriter(output_buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_lines)
        output_buf.seek(0)
        media = MediaInMemoryUpload(output_buf.read().encode('utf-8'), mimetype="text/csv")
        file_metadata = {
            'name': log_filename,
            'parents': [logs_folder_id]
        }
        service.files().create(
            body=file_metadata, media_body=media, fields='id', supportsAllDrives=True
        ).execute()

def archive_after_processing(service, user_recording_folder_id, files_to_archive_entries):
    archive_id = ensure_archive_folder(service, user_recording_folder_id)
    processed_id, processed_name = create_timestamped_processed_folder(service, archive_id)
    move_files_to_folder(service, [ent['file_id'] for ent in files_to_archive_entries], processed_id)
    print(f"Archived {len(files_to_archive_entries)} file(s) into '{processed_name}' under transcript_archive.")
    logs_folder_id = ensure_logs_folder(service, processed_id)
    append_to_csv_log(
        service,
        logs_folder_id,
        files_to_archive_entries,
        processed_id,  # archive_batch_id
        user_recording_folder_id
    )
    print(f"Batch log appended in folder {logs_folder_id}")

@log_execution_time
def generate_summary(transcript):
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": SUMMARY_INSTRUCTIONS},
                {"role": "user", "content": transcript},
            ],
            max_tokens=4096
        )
        assistant_reply = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', assistant_reply, re.DOTALL)
        if not json_match:
            logger.warning("No valid JSON found in OpenAI reply.")
            return None, None
        json_content = json_match.group(0).strip()
        parsed_json = json.loads(json_content)
        title = parsed_json.get('title', 'untitled')
        date = parsed_json.get('date', 'undated')
        filename = f"{sanitize_filename(date)}_{sanitize_filename(title)}.json"
        return json_content, filename
    except Exception as e:
        logger.exception("OpenAI summary generation failed")
        return None, None

def process_transcript_entry(service, entry):
    try:
        transcript = get_file_content_from_google_drive(service, entry['file_id'])
        if not transcript:
            return (entry, False, None, "Transcript download failed")
        json_content, output_filename = generate_summary(transcript)
        if not json_content or not output_filename:
            return (entry, False, None, "Summary failed")
        upload_content_to_google_drive(service, json_content, output_filename, OUTPUT_FOLDER_ID)
        copied_file_id = copy_file_to_folder(service, entry['file_id'], PROCESSED_FOLDER_ID)
        return (entry, True, copied_file_id, None)
    except Exception as e:
        logger.exception(f"Error processing file {entry['file_name']}")
        return (entry, False, None, str(e))

def batch_summarize_and_archive():
    logger.info("==== Gathering all Google Docs transcripts for all users...")

    for user_folder_id in RECORDING_FOLDER_IDS:
        docs_files = list_google_docs_files(authenticate_google_drive(), user_folder_id)
        if not docs_files:
            logger.info(f"No Google Docs files found in recording folder {user_folder_id}; skipping.")
            continue
        print(f"Found {len(docs_files)} transcript file(s) in {user_folder_id}")

        # 1. Ensure archive/log folders for THIS BATCH.
        try:
            service = authenticate_google_drive()
            archive_id = ensure_archive_folder(service, user_folder_id)
            processed_id, processed_name = create_timestamped_processed_folder(service, archive_id)
            logs_folder_id = ensure_logs_folder(service, processed_id)
        except Exception as e:
            logger.error(f"Could not create archive folders for {user_folder_id}: {e}")
            continue  # skip this batch if archiving isn't possible

        def archive_and_process(entry):
            """Thread-safe, per-file worker: moves file before processing."""
            local_service = authenticate_google_drive()
            file_id = entry['id']
            file_name = entry['name']

            # 2. Move transcript to batch archive folder (skip on failure)
            try:
                file = local_service.files().get(fileId=file_id, fields='parents').execute()
                prev_parents = ",".join(file.get('parents', []))
                local_service.files().update(
                    fileId=file_id,
                    addParents=processed_id,
                    removeParents=prev_parents,
                    fields='id, parents',
                    supportsAllDrives=True
                ).execute()
                logger.info(f"Moved {file_name} to archive folder {processed_id}")
            except Exception as move_error:
                logger.error(f"Could not archive {file_name} ({file_id}); skipping: {move_error}")
                return None  # Don't waste CPU/OpenAI for failed-to-archive file

            # 3. Proceed with processing (summarize etc)
            try:
                transcript = get_file_content_from_google_drive(local_service, file_id)
                if not transcript: raise Exception("Transcript download failed")
                json_content, output_filename = generate_summary(transcript)
                if not json_content or not output_filename:
                    raise Exception("Summary failed")
                upload_content_to_google_drive(local_service, json_content, output_filename, OUTPUT_FOLDER_ID)
                copy_file_to_folder(local_service, file_id, PROCESSED_FOLDER_ID)
                logger.info(f"Processed {file_name} successfully")
                return {"file_id": file_id, "file_name": file_name}
            except Exception as summary_error:
                logger.error(f"FAILED on {file_name}: {summary_error}")
                return None

        # 4. Parallel batch (archive and process)
        files_to_log = []
        with ThreadPoolExecutor(max_workers=min(5, len(docs_files))) as executor:
            futures = [executor.submit(archive_and_process, entry) for entry in docs_files]
            for future in as_completed(futures):
                res = future.result()
                if res: files_to_log.append(res)

        # 5. Log result of this batch for this user to CSV in logs folder
        if files_to_log:
            append_to_csv_log(authenticate_google_drive(), logs_folder_id, files_to_log, processed_id, user_folder_id)
            print(f"Batch log appended ({len(files_to_log)} file(s)) for user folder {user_folder_id}")

    print("All batches complete.")

if __name__ == "__main__":
    batch_summarize_and_archive()