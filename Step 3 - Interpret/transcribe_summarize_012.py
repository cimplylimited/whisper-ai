import os
import json
import re
import io
import time
import logging
from functools import wraps
import argparse

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload
from googleapiclient.errors import HttpError

from openai import OpenAI

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
# Decorator for Timing
# ==========================
def log_execution_time(func):
    """Decorator to log the execution time of functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Starting function '{func.__name__}'")
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.debug(
            f"Function '{func.__name__}' completed in {elapsed_time:.4f} seconds")
        return result
    return wrapper

# ==========================
# User-Defined Variables
# ==========================
PARENT_FOLDER_ID = 'your-user-folders-parent-id'
PROCESSED_FOLDER_ID = 'your-processed-folder-id'
OUTPUT_FOLDER_ID = '1BMl7SD0pWs6Z36UErOnYEVIddQ5eu_O5'
SERVICE_ACCOUNT_FILE = '/Users/johndoe/.key/google_cloudservices/meet-recording-management-b7cc24109698.json'

# For single-file mode: set your file ID here if you want to hard-code it (can be overridden by CLI)
SINGLE_FILE_ID = '1imZ8MiBZkY_z_EIqbLqqXyT0mEG77i78SpMWPX0o_3A'

# OpenAI model config
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-2025-04-14")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("Please set the OPENAI_API_KEY environment variable.")
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")
client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================
# Main Prompt (for OpenAI)
# ==========================
SUMMARY_INSTRUCTIONS = """
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

**Remember:**  
Your goal is to **leave no detail behind**, capture every nuance, and provide a summary that allows the team to reconstruct the full meeting context if needed, **without attributing each bullet to a specific person.**


Here is the required JSON format:

{
  "title": "Extracted Meeting Title",
  "date": "Extracted Meeting Date and Time",
  "attendees": ["Attendee1", "Attendee2"],
  "summary": "Comprehensive summary.",
  "outline": [
    {"heading": "Main Topic", "points": ["Point 1", "Point 2"]}
  ],
  "key_takeaways": ["Takeaway 1", "Takeaway 2"],
  "next_steps": [
    {
      "task": "Description",
      "owner": "Name",
      "due_date": "Target date",
      "urgency_score": "number",
      "priority_score": "number"
      "citation": "string"
    }
  ],
  "strategic_initiatives": {
    "Topic A": ["Initiative 1", "Initiative 2"]
  },
  "executive_followup": {
    "Topic A": ["Item 1", "Item 2"]
  }
}
"""

# ==========================
# Utility Functions
# ==========================
def sanitize_filename(value):
    """Sanitize a string to be used as a filename."""
    value = re.sub(r'[^\w\s-]', '', value)
    value = re.sub(r'[\s-]+', '_', value)
    return value.strip()[:100]

def redact_pii(text):
    """
    Redacts common PII (names, emails) from text with a token; returns (redacted_text, {token:original} map).
    Expand for your needs in production!
    """
    redaction_map = {}

    # Redact emails
    def email_replacer(match):
        email = match.group()
        token = f"<EMAIL-{len(redaction_map)+1}>"
        redaction_map[token] = email
        return token
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', email_replacer, text)
    
    # Redact names (very basic, needs refining for real use!)
    def name_replacer(match):
        name = match.group()
        token = f"<NAME-{len(redaction_map)+1}>"
        redaction_map[token] = name
        return token
    text = re.sub(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', name_replacer, text)

    return text, redaction_map

# ==========================
# Google Drive Functions
# ==========================
@log_execution_time
def authenticate_google_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

@log_execution_time
def list_folders(service, parent_folder_id):
    results = service.files().list(
        q=f"'{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        pageSize=1000, fields="files(id, name)").execute()
    return results.get('files', [])

@log_execution_time
def list_google_docs_files(service, folder_id):
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.document' and trashed = false",
        pageSize=1000, fields="files(id, name, mimeType)").execute()
    return results.get('files', [])

@log_execution_time
def get_file_content_from_google_drive(service, file_id):
    file = service.files().get(fileId=file_id, fields='mimeType, name').execute()
    if file['mimeType'] == 'application/vnd.google-apps.document':
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
    logger.warning(f"Unsupported MIME type: {file['mimeType']}")
    return None

@log_execution_time
def upload_content_to_google_drive(service, content, filename, folder_id):
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaInMemoryUpload(content.encode('utf-8'), mimetype='application/json')
    service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True  # <--- THIS IS THE KEY
    ).execute()

@log_execution_time
def move_file_to_folder(service, file_id, new_parent_id):
    file = service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))
    service.files().update(
        fileId=file_id,
        addParents=new_parent_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()

# ==========================
# OpenAI Summarization Function
# ==========================
@log_execution_time
def generate_summary(transcript):
    """
    Uses OpenAI v1.x client.responses.create (GPT-4.1) to produce summary JSON.
    transcript: string (already redacted if necessary)
    """
    try:
        response = client.responses.create(
            model=MODEL_NAME,
            instructions=SUMMARY_INSTRUCTIONS,
            input=transcript,
        )
        assistant_reply = response.output_text
        json_match = re.search(r'\{.*\}', assistant_reply, re.DOTALL)
        if json_match:
            json_content = json_match.group(0).strip()
        else:
            logger.warning("Could not find JSON content in the assistant's reply.")
            return None, None

        # Validate JSON
        try:
            parsed_json = json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.exception("JSON parsing error:")
            return None, None

        # Build a suggested output filename
        title = parsed_json.get('title', 'untitled')
        date = parsed_json.get('date', 'undated')
        sanitized_title = sanitize_filename(title)
        sanitized_date = sanitize_filename(date)
        output_filename = f"{sanitized_date}_{sanitized_title}.json"

        logger.info(f"Generated output filename: {output_filename}")
        return json_content, output_filename

    except Exception as e:
        logger.exception(f"An error occurred while generating summary: {e}")
        return None, None

# ==========================
# Single File Processing Function
# ==========================
def process_single_google_doc(file_id):
    """Process just one Google Docs file by file_id, from Drive -> summary via OpenAI."""
    service = authenticate_google_drive()

    # Step 1: Download
    transcript_content = get_file_content_from_google_drive(service, file_id)
    if not transcript_content:
        print(f"Failed to retrieve content for file ID {file_id}")
        return

    # Step 2: Redact PII
    # redacted_content, pii_map = redact_pii(transcript_content)
    # print(f"Redacted PII tokens: {pii_map}")

    # Step 3: Generate summary via OpenAI
    json_content, output_filename = generate_summary(transcript_content)
    if json_content:
        print(f"\nGenerated JSON Summary (also written to '{output_filename}'):\n")
        print(json_content)
        # Optionally, save locally or upload to Drive:
        with open(output_filename, "w", encoding="utf-8") as f:
             f.write(json_content)
        upload_content_to_google_drive(service, json_content, output_filename, OUTPUT_FOLDER_ID)
    else:
        print("Failed to generate summary.")

# ==========================
# Main Batch Execution Block
# ==========================
@log_execution_time
def main():
    logger.info("Script execution started.")

    service = authenticate_google_drive()
    user_folders = list_folders(service, PARENT_FOLDER_ID)
    if not user_folders:
        logger.warning("No user folders found. Exiting.")
        return

    for folder in user_folders:
        folder_id = folder['id']
        folder_name = folder['name']
        logger.info(f"Processing folder: {folder_name}")

        docs_files = list_google_docs_files(service, folder_id)
        if not docs_files:
            logger.info(f"No Google Docs files found in folder: {folder_name}")
            continue

        for file in docs_files:
            file_id = file['id']
            file_name = file['name']
            logger.info(f"Processing file: {file_name}")

            transcript_content = get_file_content_from_google_drive(service, file_id)
            if not transcript_content:
                logger.warning(f"Failed to retrieve content for file {file_name}")
                continue

            # Redact PII before sending to OpenAI API
            redacted_content, pii_map = redact_pii(transcript_content)
            logger.info(f"Redacted {len(pii_map)} PII tokens from transcript.")

            # Generate the summary (JSON output)
            json_content, output_filename = generate_summary(transcript=redacted_content)

            if json_content and output_filename:
                try:
                    upload_content_to_google_drive(service, json_content, output_filename, OUTPUT_FOLDER_ID)
                except Exception as e:
                    logger.exception(f"Failed to upload summary for file {file_name}.")
                    continue

                try:
                    move_file_to_folder(service, file_id, PROCESSED_FOLDER_ID)
                except Exception as e:
                    logger.exception(f"Failed to move file {file_name} to processed folder.")
            else:
                logger.warning(f"Failed to generate summary for file {file_name}.")

    logger.info("Script execution completed.")

# ==========================
# Script Entry Point with CLI Flags
# ==========================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Summarize Google Docs meeting transcripts using OpenAI GPT-4.1."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--batch",
        action="store_true",
        help="Run in batch mode: process all user folders."
    )
    group.add_argument(
        "--single-file",
        metavar="FILE_ID",
        type=str,
        help="Process a single Google Docs file by file ID. If omitted, uses SINGLE_FILE_ID from script."
    )
    args = parser.parse_args()

    if args.batch:
        print("Running in batch mode (all user folders).")
        main()
    elif args.single_file:
        file_id = args.single_file
        print(f"Processing single file (from CLI flag): {file_id}")
        process_single_google_doc(file_id)
    elif SINGLE_FILE_ID and SINGLE_FILE_ID != 'your-google-doc-file-id':
        print(f"Processing single file (from SINGLE_FILE_ID variable): {SINGLE_FILE_ID}")
        process_single_google_doc(SINGLE_FILE_ID)
    else:
        print("You must specify --batch or --single-file <FILE_ID>, or set SINGLE_FILE_ID in the script.")
        exit(1)