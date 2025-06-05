import os
import base64
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText



load_dotenv()
print("CWD:", os.getcwd())
print("SERVICE_ACCOUNT_FILE:", os.getenv("SERVICE_ACCOUNT_FILE"))
print("USER_TO_IMPERSONATE:", os.getenv("USER_TO_IMPERSONATE"))


# === CONFIGURATION FROM .env ===

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
USER_TO_IMPERSONATE = os.getenv("USER_TO_IMPERSONATE")
ALIAS_FROM = os.getenv("ALIAS_FROM")
TO_EMAIL = os.getenv("TO_EMAIL")
LOG_FILE = os.getenv("LOG_FILE") 
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Debug: print what variables are actually loaded!
print("CWD:", os.getcwd())
print(f"SERVICE_ACCOUNT_FILE: '{SERVICE_ACCOUNT_FILE}'")
print(f"USER_TO_IMPERSONATE: '{USER_TO_IMPERSONATE}'")
print(f"ALIAS_FROM: '{ALIAS_FROM}'")
print(f"TO_EMAIL: '{TO_EMAIL}'")
print(f"LOG_FILE: '{LOG_FILE}'")


def get_gmail_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
        subject=USER_TO_IMPERSONATE
    )
    return build('gmail', 'v1', credentials=credentials)

def send_gmail_log_as_alias(service, user, alias_from_addr, subject, body_text, recipient):
    message = MIMEText(body_text)
    message["to"] = recipient
    message["from"] = alias_from_addr
    message["subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_message = service.users().messages().send(userId=user, body={"raw": raw_message}).execute()
    print("Log sent via Gmail API as alias.")

if __name__ == "__main__":
    # Read your log file
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            log_body = f.read()
    else:
        log_body = "Job complete—no log file found!"

    # Count errors in the log
    error_count = log_body.count("ERROR")

    # Compose message
    message_text = (
        f"The transcript notes were completed with: {error_count} error(s).\n\n"
        "---- Log Tail (last 6000 characters) ----\n"
        f"{log_body[-6000:]}"
    )

    # Send email
    service = get_gmail_service()
    send_gmail_log_as_alias(
        service,
        USER_TO_IMPERSONATE,
        ALIAS_FROM,
        "Whisper AI Batch Job Log",
        message_text,
        TO_EMAIL
    )