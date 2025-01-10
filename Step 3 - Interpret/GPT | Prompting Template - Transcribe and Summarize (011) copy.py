import os
import json
import re
import io
import time
import logging
import openai
from functools import wraps
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload
from googleapiclient.errors import HttpError

# ==========================
# Logging Configuration
# ==========================

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('script.log')
console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

# Create formatters and add them to handlers
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
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

# Google Drive folder IDs
PARENT_FOLDER_ID = '1WLbDXgEzu1vn1mnSlCYNDF_xWA6k7sYo'     # Replace with your parent folder ID containing user folders
PROCESSED_FOLDER_ID = '1WLbDXgEzu1vn1mnSlCYNDF_xWA6k7sYo'  # Replace with your processed folder ID
OUTPUT_FOLDER_ID = '1w62_zSHSFGoQy751phPEnO9jbh29ZXbY'      # Replace with your output folder ID

# Path to the service account JSON key file
SERVICE_ACCOUNT_FILE = '/Users/johndoe/.key/google_cloudservices/meet-recording-management-b7cc24109698.json'  # Replace with your service account key file path

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("Please set the OPENAI_API_KEY environment variable.")
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

# OpenAI model configuration
MODEL_NAME = "gpt-3.5-turbo"  # Adjust the model as needed

# System prompt and instruction prompt
MAIN_PROMPT = """
You are a helpful assistant tasked with reviewing a meeting transcript and converting it into a structured JSON 
summary that our team can use to review and plan for the future.

Please follow these instructions:

1. **Review the meeting transcript carefully** to ensure every key point is accounted for. Do not skip any important details.

2. **Extract Meeting Details**:
   - Identify and extract the meeting title, attendees, and date/time from the transcript.
   - Include these details in the output.

3. **Organize the content** into a logical, step-by-step summary, using the specified JSON format.

4. **Create the following sections in the JSON output**:
   - **title**: The extracted meeting title.
   - **date**: The extracted meeting date and time.
   - **attendees**: A list of attendees.
   - **summary**: A comprehensive and detailed summary of the meeting's content.
   - **outline**: An array of objects, each with a "heading" and "points" that bullet out important points under each heading.
   - **key_takeaways**: A list of key decisions and conclusions.
   - **next_steps**: An array of objects, each with "task", "owner", "due_date", "urgency_score", and "priority_score".
   - **strategic_initiatives**: An object with topics as keys and arrays of initiatives as values.

5. **Ensure compliance** by making sure all steps adhere to company policies, privacy regulations, and legal requirements.

6. **Important Notes**:
   - **Output only the JSON structure in your final response**. Do not include any explanations or additional text.
   - **Ensure that the JSON is properly formatted and valid**.
   - **All strings should be enclosed in double quotes**.
   - **Use `\\n` to represent newlines within string values if necessary**.
   - **Do not include any control characters that are invalid in JSON**.

Please produce the output in the following JSON format:

{
  "title": "Extracted Meeting Title",
  "date": "Extracted Meeting Date and Time",
  "attendees": ["Attendee1", "Attendee2", "Attendee3"],
  "summary": "Comprehensive and detailed summary.",
  "outline": [
    {
      "heading": "Main Topic 1",
      "points": ["Point 1 detail", "Point 2 detail"]
    },
    {
      "heading": "Main Topic 2",
      "points": ["Point 1 detail", "Point 2 detail"]
    }
  ],
  "key_takeaways": ["Takeaway 1", "Takeaway 2"],
  "next_steps": [
    {
      "task": "Description of the task",
      "owner": "Responsible person's name",
      "due_date": "Target date",
      "urgency_score": "Index of time to complete",
      "priority_score": "Index of how important this is related to potential impact"
    }
  ],
  "strategic_initiatives": {
    "Topic A": ["Initiative 1", "Initiative 2"],
    "Topic B": ["Initiative 3", "Initiative 4"]
  }
}
"""

# Initialize the OpenAI client
openai.api_key = OPENAI_API_KEY

# ==========================
# Google Drive Functions
# ==========================

@log_execution_time
def authenticate_google_drive():
    """Authenticate using the service account and return the Google Drive service instance."""
    logger.info("Authenticating Google Drive service...")
    try:
        # Define the required scopes
        SCOPES = ['https://www.googleapis.com/auth/drive']

        # Create credentials using the service account file
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        # Build the Drive service
        service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive service authenticated successfully.")
        return service
    except Exception as e:
        logger.exception("Failed to authenticate Google Drive service.")
        raise

@log_execution_time
def list_folders(service, parent_folder_id):
    """List all folders under the given parent folder."""
    logger.info(f"Listing folders under parent folder ID: {parent_folder_id}")
    try:
        query = f"'{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(
            q=query,
            pageSize=1000,
            fields="nextPageToken, files(id, name)"
        ).execute()
        folders = results.get('files', [])
        logger.debug(f"Found {len(folders)} folders.")
        return folders
    except HttpError as error:
        logger.exception(f"An error occurred: {error}")
        return []

@log_execution_time
def list_google_docs_files(service, folder_id):
    """List all Google Docs files under the given folder."""
    logger.info(f"Listing Google Docs files in folder ID: {folder_id}")
    try:
        query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.document' and trashed = false"
        results = service.files().list(
            q=query,
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        files = results.get('files', [])
        logger.debug(f"Found {len(files)} Google Docs files.")
        return files
    except HttpError as error:
        logger.exception(f"An error occurred: {error}")
        return []

@log_execution_time
def get_file_content_from_google_drive(service, file_id):
    """Retrieve file content from Google Drive into memory."""
    logger.info(f"Retrieving content of file ID: {file_id}")
    try:
        # Get the file metadata to determine the MIME type
        file = service.files().get(fileId=file_id, fields='mimeType, name').execute()
        mime_type = file.get('mimeType')
        file_name = file.get('name')

        logger.debug(f"File name: {file_name}, MIME type: {mime_type}")

        if mime_type == 'application/vnd.google-apps.document':
            # Export Google Docs file as plain text
            request = service.files().export_media(
                fileId=file_id, mimeType='text/plain')
        else:
            logger.warning(f"Unsupported MIME type: {mime_type}")
            return None

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
            if status:
                logger.debug(
                    f"Download progress: {int(status.progress() * 100)}%")

        fh.seek(0)
        content = fh.read().decode('utf-8')
        fh.close()
        logger.info("File content retrieved successfully.")
        return content
    except HttpError as error:
        logger.exception(f"An error occurred while retrieving file content: {error}")
        return None

@log_execution_time
def upload_content_to_google_drive(service, content, filename, folder_id):
    """Upload content to Google Drive without saving to a local file."""
    logger.info(
        f"Uploading file '{filename}' to folder ID: {folder_id}")
    try:
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        media = MediaInMemoryUpload(
            content.encode('utf-8'), mimetype='application/json')
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        logger.info(f"File uploaded with ID: {file.get('id')}")
    except HttpError as error:
        logger.exception(f"An error occurred while uploading the file: {error}")
        raise

@log_execution_time
def move_file_to_folder(service, file_id, new_parent_id):
    """Move the file to the new folder."""
    logger.info(
        f"Moving file ID: {file_id} to folder ID: {new_parent_id}")
    try:
        # Retrieve the existing parents to remove
        file = service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))

        # Move the file to the new folder
        file = service.files().update(
            fileId=file_id,
            addParents=new_parent_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        logger.debug(
            f"File moved. New parents: {file.get('parents')}")
    except HttpError as error:
        logger.exception(
            f"An error occurred while moving the file: {error}")
        raise

# ==========================
# Transcript Processing Functions
# ==========================

@log_execution_time
def generate_summary(transcript):
    """Generate a summary from the transcript."""
    logger.info("Generating summary using OpenAI API.")
    try:
        # Combine the main prompt and transcript
        combined_prompt = f"{MAIN_PROMPT}\n\nTranscript:\n{transcript}"

        # Prepare the messages list
        messages = [{"role": "user", "content": combined_prompt}]

        # Call the Chat Completion API
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0  # Adjust the temperature as needed
        )
        logger.debug("OpenAI API call completed.")

        # Extract the assistant's reply
        assistant_reply = response['choices'][0]['message']['content']

        # Attempt to extract the JSON content
        json_match = re.search(r'\{.*\}', assistant_reply, re.DOTALL)
        if json_match:
            json_content = json_match.group(0).strip()
            logger.debug(
                "JSON content extracted from assistant's reply.")
        else:
            logger.warning(
                "Could not find JSON content in the assistant's reply.")
            return None, None

        # Validate the JSON output
        try:
            parsed_json = json.loads(json_content)
            logger.debug("JSON content parsed successfully.")
        except json.JSONDecodeError as e:
            logger.exception("JSON parsing error:")
            return None, None
        else:
            # Extract 'title' and 'date' to create a unique filename
            title = parsed_json.get('title', 'untitled')
            date = parsed_json.get('date', 'undated')

            # Sanitize filename components
            sanitized_title = sanitize_filename(title)
            sanitized_date = sanitize_filename(date)

            # Create the output filename
            output_filename = f"{sanitized_date}_{sanitized_title}.json"
            logger.info(f"Generated output filename: {output_filename}")
            return json_content, output_filename  # Return the JSON content and filename
    except Exception as e:
        logger.exception(
            f"An error occurred while generating the summary: {e}")
        return None, None

# ==========================
# Utility Functions
# ==========================

def sanitize_filename(value):
    """Sanitize a string to be used as a filename."""
    logger.debug(f"Sanitizing filename component: {value}")
    value = re.sub(r'[^\w\s-]', '', value)
    value = re.sub(r'[\s-]+', '_', value)
    sanitized_value = value.strip()[:100]  # Adjust length as needed
    logger.debug(f"Sanitized filename component: {sanitized_value}")
    return sanitized_value

# ==========================
# Main Execution Block
# ==========================

@log_execution_time
def main():
    logger.info("Script execution started.")

    # Authenticate and get the Google Drive service
    service = authenticate_google_drive()

    # List all folders under PARENT_FOLDER_ID
    user_folders = list_folders(service, PARENT_FOLDER_ID)

    if not user_folders:
        logger.warning("No user folders found. Exiting script.")
        return

    for folder in user_folders:
        folder_id = folder['id']
        folder_name = folder['name']
        logger.info(
            f"\nProcessing folder: {folder_name} (ID: {folder_id})")

        # List all Google Docs files in the folder
        docs_files = list_google_docs_files(service, folder_id)

        if not docs_files:
            logger.info(
                f"No Google Docs files found in folder: {folder_name}")
            continue

        for file in docs_files:
            file_id = file['id']
            file_name = file['name']
            logger.info(
                f"\nProcessing file: {file_name} (ID: {file_id})")

            # Get the transcript content from Google Drive
            transcript_content = get_file_content_from_google_drive(
                service, file_id)

            if not transcript_content:
                logger.warning(
                    f"Failed to retrieve content for file {file_name}")
                continue

            # Generate the summary
            json_content, output_filename = generate_summary(
                transcript=transcript_content)

            if json_content and output_filename:
                # Upload the output content back to Google Drive
                try:
                    upload_content_to_google_drive(
                        service, json_content, output_filename, OUTPUT_FOLDER_ID)
                except Exception as e:
                    logger.exception(
                        f"Failed to upload summary for file {file_name}.")
                    continue

                # Move the original file to PROCESSED_FOLDER_ID
                try:
                    move_file_to_folder(
                        service, file_id, PROCESSED_FOLDER_ID)
                except Exception as e:
                    logger.exception(
                        f"Failed to move file {file_name} to processed folder.")
                    continue
            else:
                logger.warning(
                    f"Failed to generate a valid JSON summary for file {file_name}.")

    logger.info("Script execution completed.")

if __name__ == "__main__":
    main()