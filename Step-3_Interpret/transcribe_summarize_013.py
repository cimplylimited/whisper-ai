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
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1")
MAX_TOKENS = 16000

# === OPENAI CLIENT ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === INSTRUCTIONS ===

SUMMARY_INSTRUCTIONS = """
ROLE
  • You are James Grant, a meticulous meeting analyst.

OUTPUT
  • Return ONLY valid JSON that matches the blank template below.
  • Top-level keys MUST appear in this exact order.
  • No extra keys, no trailing commas, all strings in double quotes.
  • FOLLOW THE EXAMPLE JSON FOR STRUCTURE WITHOUT EXCEPTION

BLANK TEMPLATE  ── FILL IT EXACTLY
{
  "title": "",
  "date": "",
  "attendees": [],
  "summary": "",
  "outline": [],
  "key_takeaways": [],
  "next_steps": [],
  "strategic_initiatives": [],
  "executive_followup": [],
  "james_grant_actions": [],
  "transcript_link": ""
}

----------------------------------------------------------------
EXTRACTION RULES
----------------------------------------------------------------
1. Read the entire transcript. Capture every materially relevant detail, decision,
   risk, action, question, or notable comment.  Omit only filler.
2. Do NOT attribute bullets to speakers unless absolutely required for context.
3. Do NOT leave out details.
4. Extract the full, deduplicated list of meeting attendees (names or roles) and provide in the "attendees" array.
  - Include all real participants/presenters identified from the transcript, even if they did not speak.
  - If only initials/roles are available, use those.
  - List in the order they appear or as listed at meeting open.

----------------------------------------------------------------
JSON EXAMPLE
----------------------------------------------------------------  
{
  "title": "",
  "date": "2025-08-10",
  "attendees": ["Alice Jobin", "Bobby Lee", "Priya Johnodon", "James Grant"],
  "summary": "The meeting established Q4 product delivery priorities, documented key customer and compliance risks, and launched new initiatives in onboarding documentation. Customer-driven reprioritization led to adjustment of the roadmap and reallocating engineering resources to single sign-on. Regulatory review for EU release was escalated. All teams aligned on updated KPIs and success metrics for the coming quarter.",
  "outline": [
    {
      "section": "Q3 Performance Review",
      "bullets": [
        "Engineering delivered 90% of planned upgrades; final UI migration deadline moved to August 15.",
        "Analytics reporting completion delayed due to staffing gap; contractor onboarding scheduled."
      ]
    },
    {
      "section": "Customer-Driven Roadmap Changes",
      "bullets": [
        "Customer feedback survey results led to reprioritization of single sign-on as a Q4 must-have.",
        "API analytics and reporting module postponed until Q1 2026."
      ]
    },
    {
      "section": "Compliance and Risk",
      "bullets": [
        "GDPR legal review opened for all EU feature releases; compliance owner assigned.",
        "New BI vendor for analytics flagged as a timeline risk; contract signature delayed."
      ]
    },
    {
      "section": "New Initiatives",
      "bullets": [
        "Onboarding documentation overhaul chartered with delivery date of November 5.",
        "Quarterly customer engagement health score pilot accepted by all teams."
      ]
    }
  ],
  "key_takeaways": [
    {
      "subject"" "Product Roadmap",
      "text": "Product roadmap shifted to prioritize customer single sign-on for Q4.",
      "category": "Product",
      "type": "Decision",
      "owner": "Product Team",
      "priority_score": 10,
      "citation": "Para 7"
    },
    {
      "subject": "ETL Pipeline Upgrade",
      "text": "API analytics upgrade postponed to Q1 2026 due to resource constraints.",
      "category": "Engineering",
      "type": "Decision",
      "owner": "Tech",
      "priority_score": 9,
      "citation": "Para 11"
    },
    {
      "subject": "EU Launch - Privacy and Compliance",
      "text": "GDPR legal review is critical risk for EU launch.",
      "category": "Compliance",
      "type": "Risk",
      "owner": "Legal",
      "priority_score": 10,
      "citation": "Para 16"
    }
  ],
  "next_steps": [
    {
      "subject": "UI Migration",
      "description": "Finalize UI migration and update tracker.",
      "owner": "Bob Lee",
      "due_date": "2025-08-17",
      "urgency_score": 8,
      "priority_score": 8,
      "citation": "Para 3",
      "high_level_topic": "Engineering"
    }
  ],
  "strategic_initiatives": [
    {
      "subject": "Customer Engagement Reporting",
      "description": "Launch quarterly customer engagement health score reporting.",
      "owner": "Priya Narayanan",
      "due_date": "2025-11-01",
      "urgency_score": 7,
      "priority_score": 8,
      "citation": "Para 24",
      "high_level_topic": "Customer Success"
    }
  ],
  "executive_followup": [
    {
      "subject": "Privacy Policy",
      "description": "Resolve GDPR review prior to all EU releases.",
      "owner": "Legal",
      "due_date": "2025-08-25",
      "urgency_score": 10,
      "priority_score": 10,
      "citation": "Para 16",
      "high_level_topic": "Compliance"
    }
  ],
  "james_grant_actions": [
    {
      "subject": "Client Onboarding",
      "description": "Approve new onboarding documentation structure for wider rollout.",
      "owner": "James Grant",
      "due_date": "2025-08-18",
      "urgency_score": 9,
      "priority_score": 9,
      "citation": "Para 27",
      "high_level_topic": "Product",
      "james_grant_reference": true
    }
  ],
  "transcript_link": "https://docs.google.com/document/d/1BMl7SD0pWs6Z36UErOnYEVIddQ5eu_O5/edit"
}

----------------------------------------------------------------
SECTION SPECIFICATIONS
----------------------------------------------------------------
Title (string):
 - If the transcript opens with a descriptive meeting title (meaningful project, group, or topic, not a random string or "untitled"), use that exactly as your "title".
 - If the title appears as a random string, video-code, or is unclear, CONSTRUCT a clear, descriptive meeting title summarizing the main focus of this transcript in 3-8 words.
 - Capitalize each principal word. No abbreviations. No parentheses. No special characters other than spaces and dashes.
 - After constructing the title, always format the final output as:
     <Descriptive-Title-With-Dashes>-_yyyy-mm-dd
   where yyyy-mm-dd is the date of the meeting.
 - Example: "Quarterly-Product-Roadmap-Review_2025-08-10"
 - No quotation marks and no double underscores. If the date is missing, use today's date.

date (string):   Meeting start date in YYYY-MM-DD.
attendees  (array)
  • All names (strings, no objects), of actual meeting attendees.
  • If no names are available, use roles, emails, or "Unknown".
  • If transcript includes no list, deduce from the opening lines and all explicit mentions.
  • Output as: [ "Person One", "Person Two", ... ]

summary  (string)
  • 5-10 paragraphs, 1-5 sentences.  Detailed but summarized.
  • Purpose, major outcomes, high-level context.  NO bullet points, NO task detail.

outline  (array of objects)
  • Each object: { "section": <string>, "bullets": [<string>, …] }
  • If no headings exist use one object:
      { "section": "General", "bullets": [ … ] }
  • Do NOT alternate heading/detail in a flat list.  Do NOT mix nested and flat lists.

key_takeaways  (array of objects)
  • Each object keys (exact order):
      subject, text, category, type, owner, priority_score, citation
  • type must be one of "Risk" "Decision" "Outcome" "Info" "Question".
  • priority_score 1-10.  3–15 total items.  Each text is a single, crisp sentence.  

----------------------------------------------------------------
ACTION OBJECT MODEL  (next_steps / strategic_initiatives / executive_followup)
----------------------------------------------------------------
Required fields (exact order):
  subject
  description
  owner
  due_date           → ISO format "YYYY-MM-DD"  (use transcript dates; if none give "N/A")
  urgency_score      → integer 1-10  (time sensitivity)
  priority_score     → integer 1-10  (business importance)
  citation           → transcript reference ("Para 12", timestamp, etc.)
  high_level_topic   → one- or two-word category (e.g., "Marketing", "Finance")

next_steps
  • Immediate tasks (< 4 weeks) assigned during the meeting.

strategic_initiatives
  • Longer horizon projects or big-impact initiatives (> 4 weeks) agreed or proposed.

executive_followup
  • Items requiring C-level review, decision, or escalation.

----------------------------------------------------------------
JAMES GRANT ACTIONS
----------------------------------------------------------------
• Same action-object fields PLUS  "james_grant_reference"  (Boolean).
• Set james_grant_reference = true if the item explicitly assigns or references
  James Grant; otherwise false.
• If none, output an empty array.

----------------------------------------------------------------
ASSIGNMENT & SCORING
----------------------------------------------------------------
• Every action/initiative/follow-up MUST have an owner.
• urgency_score = how soon action is needed (1 low, 10 immediate).
• priority_score = business impact (1 low, 10 critical).
• Provide a due_date wherever the transcript implies one; else "N/A".

----------------------------------------------------------------
CITATIONS
----------------------------------------------------------------
• Each key_takeaway object and every action object MUST include a citation field
  so the item can be traced to the transcript.

----------------------------------------------------------------
AMBIGUITY HANDLING
----------------------------------------------------------------
• If any point is unclear, flag it in the bullets or citation for follow-up.

----------------------------------------------------------------
VALIDATION CHECK BEFORE YOU OUTPUT
----------------------------------------------------------------
✓ All top-level keys present, in template order.  
✓ Each section matches its type and field list.  
✓ All action arrays use the exact 7 (or 8) fields, correct order.  
✓ All scores are integers 1-10; due_date in YYYY-MM-DD or "N/A".  
✓ Strings double-quoted; JSON is syntactically valid.

Produce ONLY the final JSON.


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

def sanitize_filename(value):
    """Returns a safe string for use in file names."""
    value = str(value)
    value = re.sub(r'[^\w\s-]', '', value)
    value = re.sub(r'[\s\-]+', '_', value).strip("_")
    return value[:80] or "untitled"

def normalize_title(parsed_json, fallback_doc_name=None):
    """Extract or fallback, returning a safe title for file naming."""
    title = parsed_json.get('title')
    if isinstance(title, str) and title.strip():
        return sanitize_filename(title)
    else:
        logger.warning("LLM JSON missing/blank 'title'. Using fallback.")
        return sanitize_filename(fallback_doc_name or "untitled")

def normalize_date(parsed_json, fallback_date=None):
    """YYYY-MM-DD if valid, else fallback/today."""
    date = parsed_json.get('date')
    if isinstance(date, str) and re.match(r'^\d{4}-\d{2}-\d{2}$', date.strip()):
        return date.strip()
    fallback = fallback_date or datetime.date.today().isoformat()
    logger.warning(f"LLM missing/invalid 'date'. Using fallback: {fallback}")
    return fallback

def generate_filename(parsed_json, fallback_doc_name, fallback_date=None):
    """Generate a robustly defensively named file."""
    date = normalize_date(parsed_json, fallback_date)
    title = normalize_title(parsed_json, fallback_doc_name)
    return f"{date}_{title}.json"

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

@log_execution_time
def process_transcript_entry(service, entry, processed_id, output_folder_id):
    """
    • Downloads the Google-Docs transcript
    • Sends it to the LLM with SUMMARY_INSTRUCTIONS
    • Injects a transcript_link into the returned JSON
    • Uploads the JSON to the OUTPUT_FOLDER_ID
    • Moves the original transcript into the processed (archive) folder
    • Returns a dict summarising success / failure for CSV logging
    """
    file_id   = entry['id']
    file_name = entry['name']
    status          = "success"
    error_message   = ""

    # ------------------------------------------------------------------ #
    # 1. Download transcript                                              #
    # ------------------------------------------------------------------ #
    try:
        transcript = get_file_content_from_google_drive(service, file_id)
        if not transcript:
            raise Exception("Transcript download returned empty content.")
    except Exception as e:
        status = "failed"
        error_message = f"Transcript download failed: {e}"
        logger.error(error_message)
        return {
            "file_id": file_id, "file_name": file_name,
            "status": status,   "error": error_message
        }

    # ------------------------------------------------------------------ #
    # 2. Create summary via OpenAI (with retry)                           #
    # ------------------------------------------------------------------ #
    json_content, output_filename = generate_summary_with_retries(transcript, retries=3)
    if not json_content or not output_filename:
        status = "failed"
        error_message = "Summary generation failed (see logs for detail)"
        logger.error(f"{error_message} for file {file_name}")
        return {
            "file_id": file_id, "file_name": file_name,
            "status": status,   "error": error_message
        }

    # ------------------------------------------------------------------ #
    # 3. Inject transcript_link into JSON                                 #
    # ------------------------------------------------------------------ #
    try:
        parsed_json = json.loads(json_content)
    except json.JSONDecodeError as e:
        status = "failed"
        error_message = f"LLM returned invalid JSON: {e}"
        logger.error(error_message)
        return {
            "file_id": file_id, "file_name": file_name,
            "status": status,   "error": error_message
        }

    # Build link (same ID even after move)
    transcript_link = f"https://docs.google.com/document/d/{file_id}/edit"
    parsed_json["transcript_link"] = transcript_link

    # Re-serialise prettily
    json_content = json.dumps(parsed_json, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------ #
    # 4. Upload summary JSON to OUTPUT_FOLDER_ID                          #
    # ------------------------------------------------------------------ #
    try:
        upload_content_to_google_drive(
            service, json_content, output_filename, output_folder_id
        )
    except Exception as e:
        status = "failed"
        error_message = f"Summary upload failed: {e}"
        logger.error(error_message)
        return {
            "file_id": file_id, "file_name": file_name,
            "status": status,   "error": error_message
        }

    # ------------------------------------------------------------------ #
    # 5. Move original transcript into archive                            #
    # ------------------------------------------------------------------ #
    try:
        old_parents = ",".join(
            service.files().get(fileId=file_id, fields='parents').execute().get('parents', [])
        )
        service.files().update(
            fileId=file_id,
            addParents=processed_id,
            removeParents=old_parents,
            fields='id, parents',
            supportsAllDrives=True
        ).execute()
        logger.info(f"Moved {file_name} to processed folder {processed_id}")
    except Exception as move_error:
        status = "failed"
        error_message = f"Could not archive {file_name}: {move_error}"
        logger.error(error_message)

    # ------------------------------------------------------------------ #
    # 6. Return result for CSV logging                                    #
    # ------------------------------------------------------------------ #
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