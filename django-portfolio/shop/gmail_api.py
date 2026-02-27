# shop/gmail_api.py
import base64
import pickle
from email.mime.text import MIMEText
from pathlib import Path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Base directory (django-portfolio/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Gmail send scope
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "gmail_token.pickle"


def _get_gmail_service():
    creds = None

    # Load saved token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # Refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


def send_gmail(to_email: str, subject: str, message: str):
    """
    Sends an email using Gmail API.
    Replaces django.core.mail.send_mail safely.
    """
    service = _get_gmail_service()

    mime_message = MIMEText(message)
    mime_message["to"] = to_email
    mime_message["subject"] = subject

    raw = base64.urlsafe_b64encode(
        mime_message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()
