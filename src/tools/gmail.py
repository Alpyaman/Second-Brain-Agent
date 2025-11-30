"""
Gmail Integration

This module provides functions to interact with Gmail API, allowing the agent to create
draft emails.
"""

import base64
from pathlib import Path
from typing import Optional
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

# Path configuration
SCRIPT_DIR = Path(__file__).parent.parent.parent
CREDENTIALS_PATH = SCRIPT_DIR / "credentials.json"
GMAIL_TOKEN_PATH = SCRIPT_DIR / "gmail_token.json"

def authenticate_gmail() -> Optional[object]:
    """
    Authenticate with Gmail API using OAuth 2.0.

    Returns:
        Gmail API service object, or None if authentication fails
    """
    creds = None

    # The gmail_token.json stores the user's access and refresh tokens
    if GMAIL_TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_PATH), SCOPES)
        except Exception as e:
            print(f"Error loading Gmail token: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired Gmail credentials...")
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing Gmail token: {e}")
                creds = None

        if not creds:
            if not CREDENTIALS_PATH.exists():
                print(f"Error: credentials.json not found at {CREDENTIALS_PATH}")
                return None
            
            try:
                print("Starting Gmail OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
                creds = flow.run_local_server(port=0)
                print("Gmail authentication successful!")
            except Exception as e:
                print(f"Gmail authentication failed: {e}")
                return None

        # Save the credentials for the next run
        try:
            with open(GMAIL_TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
            print(f"Gmail credentials saved to {GMAIL_TOKEN_PATH}")
        except Exception as e:
            print(f"Warning: Could not save Gmail credentials: {e}")

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building Gmail service: {e}")
        return None

def create_draft_email(to: str, subject: str, body: str) -> str:
    """
    Create a draft email in Gmail (does not send automatically).

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content (plain text or HTML)

    Returns:
        Success message with draft ID, or error message
    """
    print(f"Creating draft email to: {to}")
    print(f"   Subject: {subject}")

    # Authenticate
    service = authenticate_gmail()
    if not service:
        return "Failed to authenticate with Gmail. Please check your credentials."

    try:
        # Create the email message
        message = MIMEText(body, 'html' if '<' in body and '>' in body else 'plain')
        message['To'] = to
        message['Subject'] = subject

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Create the draft
        draft = {
            'message': {
                'raw': raw_message
            }
        }

        draft_result = service.users().drafts().create(userId='me', body=draft).execute()

        draft_id = draft_result['id']
        success_msg = f"Draft email created successfully!\n   Draft ID: {draft_id}\n   To: {to}\n   Subject: {subject}"
        print(success_msg)

        return success_msg

    except HttpError as error:
        error_msg = f"Gmail API error: {error}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error creating draft: {e}"
        print(error_msg)
        return error_msg

def list_drafts(max_results: int = 10) -> str:
    """
    List draft emails in Gmail.

    Args:
        max_results: Maximum number of drafts to return (default: 10)

    Returns:
        Formatted string with draft information, or error message
    """
    print(f"Fetching draft emails (max: {max_results})...")

    # Authenticate
    service = authenticate_gmail()
    if not service:
        return "Failed to authenticate with Gmail. Please check your credentials."

    try:
        # Get drafts
        results = service.users().drafts().list(userId='me', maxResults=max_results).execute()

        drafts = results.get('drafts', [])

        if not drafts:
            return "No draft emails found."

        # Format drafts
        formatted_drafts = []
        formatted_drafts.append(f"📬 Draft Emails ({len(drafts)}):")
        formatted_drafts.append("")

        for draft in drafts:
            draft_id = draft['id']
            # Get full draft details
            draft_detail = service.users().drafts().get(userId='me', id=draft_id).execute()

            message = draft_detail['message']
            headers = message['payload']['headers']

            # Extract subject and to
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            to = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')

            formatted_drafts.append(f"     ID: {draft_id}")
            formatted_drafts.append(f"     To: {to}")
            formatted_drafts.append(f"     Subject: {subject}")
            formatted_drafts.append("")

        print(f"Found {len(drafts)} draft(s)")
        return "\n".join(formatted_drafts)

    except HttpError as error:
        error_msg = f"Gmail API error: {error}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        return error_msg

if __name__ == "__main__":
    """Test the Gmail functions."""
    print("=" * 60)
    print("Gmail Integration Test")
    print("=" * 60, "\n")

    # Test creating a draft
    print("Testing create_draft_email():")
    print("-" * 60)
    result = create_draft_email(
        to="test@example.com",
        subject="Test Draft from Second-Brain-Agent",
        body="This is a test draft email created by your AI Chief of Staff.\n\nThis draft was created for testing purposes and can be safely deleted."
    )
    print(result)

    print("\n", "=" * 60, "\n")

    # Test listing drafts
    print("Testing list_drafts():")
    print("-" * 60)
    result = list_drafts()
    print(result)
    print("\n", "=" * 60)