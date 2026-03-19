# shop/gmail_api.py

import base64
import pickle
from email.mime.text import MIMEText
from pathlib import Path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

# Base directory (django-portfolio/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Gmail send scope
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "gmail_token.pickle"


def _get_gmail_service():
    creds = None

    # ✅ Load saved token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # ✅ Refresh or authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(Request())

        else:
            print("🔐 Generating Gmail Token...")

            flow = Flow.from_client_secrets_file(
                CREDENTIALS_FILE,
                scopes=SCOPES,
                redirect_uri="http://localhost:8080/"
            )

            auth_url, _ = flow.authorization_url(prompt='consent')

            print("\n🔗 Open this URL in your browser:\n")
            print(auth_url)

            code = input("\n📥 Enter the authorization code: ")

            flow.fetch_token(code=code)
            creds = flow.credentials

        # ✅ Save token
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


def send_gmail(to_email: str, subject: str, message: str):
    """
    Sends email using Gmail API
    """

    service = _get_gmail_service()

    msg = MIMEText(message)
    msg["to"] = to_email
    msg["subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    body = {"raw": raw}

    service.users().messages().send(userId="me", body=body).execute()

    print(f"✅ Email sent to {to_email}")


# ✅ OPTIONAL: run manually to generate token
if __name__ == "__main__":
    print("🔐 Running Gmail setup...")
    _get_gmail_service()
    print("✅ Token generated successfully!")
