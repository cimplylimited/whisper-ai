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

# === LOGGING CONFIGURATION ===
## JUST REMEMBER THAT I WANT TO LOOK AT THE LOG OUTPUT AND ROUTE TO GDRIVE STANDING FOLDER**
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('script.log')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# === LOAD CONFIG (.env or ENVIRONMENT) ===
load_dotenv()
RECORDING_FOLDER_IDS = ast.literal_eval(os.getenv("RECORDING_FOLDER_IDS", "[]"))
PROCESSED_FOLDER_ID = os.getenv("PROCESSED_FOLDER_ID")
OUTPUT_FOLDER_ID = os.getenv("OUTPUT_FOLDER_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-2025-04-14")
MAX_TOKENS = 16000

# === OPENAI CLIENT ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === INSTRUCTIONS ===
SUMMARY_INSTRUCTIONS = """
Your name is James Grant.  You are a highly meticulous, detail-oriented meeting analyst. Your task is to review the following meeting transcript and produce a comprehensive, structured summary in JSON format for executive and operational use.

Instructions:

Extraction (Do not summarize yet):

Carefully read the entire transcript.
Identify every key point, decision, action item, open question, and any notable comment—no matter how minor.
Do not attribute each point to a specific speaker in your summary bullets, unless the identity is essential for understanding the point.
For each bullet, focus on the content, detail, and context not who said it.
Do not omit any information that could be relevant to any attendee or future planning.
Task and Ownership Assignment:

Pay attention to who assigns tasks, who volunteers, or is delegated action items.
When creating the next_steps section, use the transcript’s speaker information to assign owners to each task as accurately as possible.
Consider the relative priority and relative urgency of each assigned task on a scale of 1-10
Categorization:

Group extracted points into logical sections (e.g., topics, agenda items).
Tag any item that is especially important, controversial, or actionable.
Detailed Summarization:

For each group/section, write a detailed summary using granular, content-rich bullet points.
Do not generalize or omit specifics—be as detailed as possible.
Do not include speaker names in summary bullets unless essential for context.
Structured Output:

Populate the required JSON structure:
title, date, attendees, summary, outline (with detailed bullet points), key_takeaways, next_steps (with all required fields), strategic_initiatives, james_grant_items.
For all array fields (like outline, key_takeaways), use detailed, granular bullet points.
For next_steps, ensure each task is specific and assigns an owner, based on who was given or accepted the task in the transcript.
It is critical the template is followed for consistency in data parsing
Special Emphasis:

Pay extra attention to anything related to "James Grant" and ensure all such items are included in the james_grant_items section.
You are James Grant and these tasks require a separate thought process
They signal that as our assistant it is important to both partners to find these items and consider them in the context they were spoken
This will often relate to other parts of the business and may require some inference to determine where they should be reclassed and added for later discussion
Flag any ambiguous or unclear points for follow-up. If something appears important but you do not understand we want you to tell us.
Self-Check:

Before producing the final output, review your extracted points and summaries to ensure nothing from the transcript is omitted or oversimplified.
Proof read and insert citations so we can attribute later.
Output:

Output only valid JSON as per the specified format, with all strings in double quotes and newlines as \n.
For the next_steps, strategic_initiatives, and executive_followup fields, each must be an array of objects. Each object must use the following fields only, in this exact order and with these names:

description
owner
due_date
urgency_score
priority_score
citation
high_level_topic
Apply this format for all items in all three sections, with no field additions or omissions.

10. After the "executive_followup" section, create a new field called "james_grant_actions".
This must be an array of objects.
Each object must contain the following fields, exactly as listed, in this order:

description
owner
due_date
urgency_score
priority_score
citation
high_level_topic
james_grant_reference
For each actionable item, set james_grant_reference to true if "James Grant" is mentioned or assigned within the transcript for that item, otherwise false.
If there are no references to "James Grant" in the transcript, set "james_grant_actions" to an empty array.

This section must use the identical structure as the other actionable arrays but with the added james_grant_reference Boolean flag.

Remember:
Your goal is to leave no detail behind, capture every nuance, and provide a summary that allows the team to reconstruct the full meeting context if needed, without attributing each bullet to a specific person.

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
    fieldnames = [
        "original_file_id",
        "file_name",
        "archive_batch_id",
        "date_moved",
        "user_folder_id",
        "status",
        "error"
    ]
    now = datetime.datetime.now().isoformat()
    new_lines = [
        {
            "original_file_id": ent.get('file_id', ''),
            "file_name": ent.get('file_name', ''),
            "archive_batch_id": archive_batch_id,
            "date_moved": now,
            "user_folder_id": user_folder_id,
            "status": ent.get('status', ''),
            "error": ent.get('error', '')
        }
        for ent in entries if ent is not None and "file_id" in ent
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

def generate_summary_with_retries(transcript, retries=3, base_backoff=10):
    for attempt in range(1, retries+1):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": SUMMARY_INSTRUCTIONS},
                    {"role": "user", "content": transcript},
                ],
                max_tokens=MAX_TOKENS
            )
            assistant_reply = response.choices[0].message.content

            logger.warning(f"OpenAI raw reply: {assistant_reply}")

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
            logger.warning(f"OpenAI API call failed on attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                sleep_time = base_backoff * attempt
                logger.info(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error("OpenAI summary generation failed after retries.")
    return None, None

def process_transcript_entry(service, entry, processed_id, output_folder_id):
    file_id = entry['id']
    file_name = entry['name']
    status = "success"
    error_message = ""

    # 1. Download transcript
    try:
        transcript = get_file_content_from_google_drive(service, file_id)
        if not transcript:
            raise Exception("Transcript download failed")
    except Exception as e:
        status = "failed"
        error_message = f"Transcript download failed: {e}"
        logger.error(error_message)
        return {
            "file_id": file_id,
            "file_name": file_name,
            "status": status,
            "error": error_message
        }

    # 2. Create summary (with retry)
    json_content, output_filename = generate_summary_with_retries(transcript, retries=3)
    if not json_content or not output_filename:
        status = "failed"
        error_message = "Summary generation failed (see logs for detail)"
        logger.error(f"{error_message} for file {file_name}")
        return {
            "file_id": file_id,
            "file_name": file_name,
            "status": status,
            "error": error_message
        }

    # 3. Upload summary
    try:
        upload_content_to_google_drive(service, json_content, output_filename, output_folder_id)
    except Exception as e:
        status = "failed"
        error_message = f"Summary upload failed: {e}"
        logger.error(error_message)
        return {
            "file_id": file_id,
            "file_name": file_name,
            "status": status,
            "error": error_message
        }

    # 4. Move file to archive (processed_id)
    try:
        file = service.files().get(fileId=file_id, fields='parents').execute()
        prev_parents = ",".join(file.get('parents', []))
        service.files().update(
            fileId=file_id,
            addParents=processed_id,
            removeParents=prev_parents,
            fields='id, parents',
            supportsAllDrives=True
        ).execute()
        logger.info(f"Moved {file_name} to archive folder {processed_id}")
    except Exception as move_error:
        status = 'failed'
        error_message = f"Could not archive {file_name} ({file_id}): {move_error}"
        logger.error(error_message)
        return {
            "file_id": file_id,
            "file_name": file_name,
            "status": status,
            "error": error_message
        }
    return {
        "file_id": file_id,
        "file_name": file_name,
        "status": status,
        "error": error_message
    }

def batch_summarize_and_archive():
    logger.info("==== Gathering all Google Docs transcripts for all users...")

    for user_folder_id in RECORDING_FOLDER_IDS:
        service = authenticate_google_drive()
        docs_files = list_google_docs_files(service, user_folder_id)
        if not docs_files:
            logger.info(f"No Google Docs files found in recording folder {user_folder_id}; skipping.")
            continue
        print(f"Found {len(docs_files)} transcript file(s) in {user_folder_id}")

        # Prepare archive/log folders for THIS BATCH (per folder processed)
        try:
            archive_id = ensure_archive_folder(service, user_folder_id)
            processed_id, processed_name = create_timestamped_processed_folder(service, archive_id)
            logs_folder_id = ensure_logs_folder(service, processed_id)
        except Exception as e:
            logger.error(f"Could not create archive folders for {user_folder_id}: {e}")
            continue

        files_to_log = []
        with ThreadPoolExecutor(max_workers=min(5, len(docs_files))) as executor:
            futures = [
                executor.submit(
                    process_transcript_entry, authenticate_google_drive(), entry,
                    processed_id, OUTPUT_FOLDER_ID
                )
                for entry in docs_files
            ]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    files_to_log.append(res)

        append_to_csv_log(service, logs_folder_id, files_to_log, processed_id, user_folder_id)

        num_failed = sum(1 for x in files_to_log if x.get('status') == 'failed')
        num_success = sum(1 for x in files_to_log if x.get('status') == 'success')
        print(f"Batch for {user_folder_id}: {num_success} succeeded, {num_failed} failed")

    print("All batches complete.")

if __name__ == "__main__":
    batch_summarize_and_archive()