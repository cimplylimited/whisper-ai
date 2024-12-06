import os
import json
import re
import io
from openai import OpenAI
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload
from googleapiclient.errors import HttpError

# ==========================
# User-Defined Variables
# ==========================

# Google Drive file and folder IDs
TRANSCRIPT_FILE_ID = '1qBTYT0n9oV4smzjpEgCYEARE7c_v65UzMZW-WnCQ6PY'  # Replace with your transcript file ID
OUTPUT_FOLDER_ID = '19znkdIQco-F39dTArhQ--iy8n3l8qEAf'      # Replace with your output folder ID

# OAuth directory path for storing credentials
OAUTH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.oauth')  # Default is './.oauth' inside the package directory

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# OpenAI model configuration
MODEL_NAME = "o1-preview"  # Adjust the model as needed

# System prompt and instruction prompt
MAIN_PROMPT = """
You are a helpful assistant tasked with reviewing a meeting transcript and converting it into a structured JSON summary that our team can use to review and plan for the future.

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

# Paths for OAuth credentials
CREDENTIALS_PATH = os.path.join(OAUTH_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(OAUTH_DIR, 'token.json')

# Initialize the OpenAI client using the environment variable for the API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")
client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================
# Google Drive Functions
# ==========================

def authenticate_google_drive():
    """Authenticate the user and return the Google Drive service instance."""
    creds = None

    # Ensure the OAuth directory exists
    if not os.path.exists(OAUTH_DIR):
        os.makedirs(OAUTH_DIR, mode=0o700)

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"Credentials file not found at {CREDENTIALS_PATH}.")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use with secure permissions
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
        os.chmod(TOKEN_PATH, 0o600)
    # Build the Drive service
    service = build('drive', 'v3', credentials=creds)
    return service

def get_file_content_from_google_drive(service, file_id):
    """Retrieve file content from Google Drive into memory."""
    try:
        # First, get the file metadata to determine the MIME type
        file = service.files().get(fileId=file_id, fields='mimeType, name').execute()
        mime_type = file.get('mimeType')
        file_name = file.get('name')

        print(f"Retrieving file '{file_name}' with ID {file_id}...")

        if mime_type == 'application/vnd.google-apps.document':
            # Export Google Docs file as plain text
            request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        elif mime_type == 'application/vnd.google-apps.presentation':
            # Export Google Slides file as plain text
            request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            # Export Google Sheets file as CSV
            request = service.files().export_media(fileId=file_id, mimeType='text/csv')
        else:
            # For other file types, download the binary content
            request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download {int(status.progress() * 100)}% complete.")

        fh.seek(0)
        content = fh.read().decode('utf-8')
        fh.close()
        print("File content retrieved successfully.")
        return content
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def upload_content_to_google_drive(service, content, filename, folder_id):
    """Upload content to Google Drive without saving to a local file."""
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaInMemoryUpload(content.encode('utf-8'), mimetype='application/json')
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    print(f"File uploaded with ID: {file.get('id')}")

# ==========================
# Transcript Processing Functions
# ==========================

def generate_summary(transcript):
    """Generate a summary from the transcript."""
    # Combine the main prompt and transcript
    combined_prompt = f"{MAIN_PROMPT}\n\nTranscript:\n{transcript}"

    # Prepare the messages list
    messages = [{"role": "user", "content": combined_prompt}]

    # Prepare parameters for the API call
    api_params = {
        'model': MODEL_NAME,
        'messages': messages
    }

    # Add 'temperature' parameter if supported
    if is_temperature_supported(MODEL_NAME):
        api_params['temperature'] = 0  # Set to your desired value

    # Call the Chat Completion API
    response = client.chat.completions.create(**api_params)

    # Extract the assistant's reply
    assistant_reply = response.choices[0].message.content

    # Print the assistant's reply for debugging
    print("Assistant's reply:")
    print(assistant_reply)

    # Attempt to extract the JSON content
    json_match = re.search(r'\{.*\}', assistant_reply, re.DOTALL)
    if json_match:
        json_content = json_match.group(0).strip()
    else:
        print("Could not find JSON content in the assistant's reply.")
        return None, None

    # Validate the JSON output
    try:
        parsed_json = json.loads(json_content)
    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)
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
        return json_content, output_filename  # Return the JSON content and filename

# ==========================
# Utility Functions
# ==========================

def is_temperature_supported(model_name):
    """Check if the model supports the 'temperature' parameter."""
    temperature_supported_models = ['gpt-3.5-turbo', 'gpt-4']
    return model_name in temperature_supported_models

def sanitize_filename(value):
    """Sanitize a string to be used as a filename."""
    value = re.sub(r'[^\w\s-]', '', value)
    value = re.sub(r'[\s-]+', '_', value)
    return value.strip()[:100]  # Adjust length as needed

# ==========================
# Main Execution Block
# ==========================

if __name__ == "__main__":
    # Authenticate and get the Google Drive service
    service = authenticate_google_drive()

    # Get the transcript content from Google Drive
    TRANSCRIPT_CONTENT = get_file_content_from_google_drive(service, TRANSCRIPT_FILE_ID)

    # Generate the summary
    JSON_CONTENT, OUTPUT_FILENAME = generate_summary(transcript=TRANSCRIPT_CONTENT)

    if JSON_CONTENT and OUTPUT_FILENAME:
        # Upload the output content back to Google Drive
        upload_content_to_google_drive(service, JSON_CONTENT, OUTPUT_FILENAME, OUTPUT_FOLDER_ID)
    else:
        print("Failed to generate a valid JSON summary.")
