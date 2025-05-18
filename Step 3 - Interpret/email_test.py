import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64



load_dotenv()
print("CWD:", os.getcwd())
print("SERVICE_ACCOUNT_FILE:", os.getenv("SERVICE_ACCOUNT_FILE"))
print("USER_TO_IMPERSONATE:", os.getenv("USER_TO_IMPERSONATE"))

# -- Load variables from .env --

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
USER_TO_IMPERSONATE = os.getenv("ALIAS_FROM")
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

if not SERVICE_ACCOUNT_FILE or not USER_TO_IMPERSONATE:
    print("SERVICE_ACCOUNT_FILE and USER_TO_IMPERSONATE must be set in .env")
    exit(1)

# -- Build credentials and API client --
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES,
    subject=USER_TO_IMPERSONATE,
)
service = build('gmail', 'v1', credentials=credentials)

# -- Compose and send test message --
body = "Test email from batch job script."
message = MIMEText(body)
message['to'] = USER_TO_IMPERSONATE   # Change to any recipient for a real test
message['from'] = USER_TO_IMPERSONATE
message['subject'] = "Test Gmail API Service Account"
raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

service.users().messages().send(
    userId=USER_TO_IMPERSONATE,
    body={'raw': raw}
).execute()

print("Sent!")