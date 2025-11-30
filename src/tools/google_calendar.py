"""
Google Calendar Integration

This module provides functions to interact with Google Calendar API, allowing the agent
to view and query calendar events.
"""

import datetime
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Path configuration
SCRIPT_DIR = Path(__file__).parent.parent.parent
CREDENTIALS_PATH = SCRIPT_DIR / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "token.json"

def authenticate_google_calendar() -> Optional[object]:
    """
    Authenticate with Google Calendar API using OAuth 2.0.

    Returns:
        Google Calendar API service object, or None if authentication fails
    """
    creds = None

    # The token.json stores the user's access and refresh tokens
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        
        except Exception as e:
            print(f"Error loading token: {e}")

    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None

        if not creds:
            if not CREDENTIALS_PATH.exists():
                print(f"Error: credentials.json not found at {CREDENTIALS_PATH}")
                return None

            try:
                print("Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
                creds = flow.run_local_server(port=0)
                print("Authentication successful!")
            except Exception as e:
                print(f"Authentication failed: {e}")
                return None
        
        # Save the credentials for the next run
        try:
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
            print(f"Credentials saved to {TOKEN_PATH}")
        except Exception as e:
            print(f"Warning: Could not save credentials: {e}")

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building Calendar service: {e}")
        return None
    
def get_todays_event(max_results: int = 10) -> str:
    """
    Get today's calendar events and return them as a formatted string.

    Args:
        max_results = Maximum number of events to return (default: 10)

    Returns:
        Formatted string with today's events (Time - Summary), or error message
    """
    print("Fetching today's calendar events...")

    # Authenticate
    service = authenticate_google_calendar()
    if not service:
        return "Failed to authenticate with Google Calendar."
    
    try:
        # Get today's date range
        now = datetime.datetime.now()
        today_start = datetime.datetime.combine(now.date(), datetime.time.min)
        today_end = datetime.datetime.combine(now.date(), datetime.time.max)

        # Conver to RFC3339 format
        time_min = today_start.isoformat() + 'Z'
        time_max = today_end.isoformat() + 'Z'

        # Call the Calendar API
        print(f"Searching for events on {now.strftime('%Y-%m-%d')}")
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return f"No events scheduled for today ({now.strftime('%A, %B %d, %Y')})."
        
        # Format events
        formatted_events = []
        formatted_events.append(f"Events for {now.strftime('%A, %B %d, %Y')}:")
        formatted_events.append("")

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')

            # Parse the time
            if 'T' in start:
                # It's a datetime
                start_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                time_str = start_time.strftime('%I:%M %p')
            else:
                # It's an all-day event
                time_str = 'All Day'

            # Get Optional fields
            location = event.get('location', '')
            description = event.get('description', '')

            # Format the event
            event_line = f" {time_str} - {summary}"
            if description:
                event_line += f": {description}"
            if location:
                event_line += f" ({location})"

            formatted_events.append(event_line)

        print(f"Found {len(events)} event(s)")
        return "\n".join(formatted_events)
    
    except HttpError as error:
        error_msg = f"An error occured: {error}"
        print(error_msg)
        return error_msg
    except Exception as e:
        print(f"Unexpected error: {e}")
        return e
    
def get_events_in_range(days_ahead: int = 7, max_results: int = 20) -> str:
    """
    Get calendar events for the next N days.

    Args:
        days_ahead: Number of days to look ahead (default: 7)
        max_results: Maximum number of events to return (default: 20)

    Returns:
        Formatted string with upcoming events
    """
    print(f"Fetching events for the next {days_ahead} days...")

    # Authenticate
    service = authenticate_google_calendar()
    if not service:
        return "Failed to authenticate with Google Calendar. Please check your credentials."

    try:
        # Get date range
        now = datetime.datetime.now()
        time_min = now.isoformat() + 'Z'

        end_date = now + datetime.timedelta(days=days_ahead)
        time_max = end_date.isoformat() + 'Z'

        # Call the Calendar API
        print(f"Searching from {now.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime').execute()

        events = events_result.get('items', [])

        if not events:
            return f"No events scheduled for the next {days_ahead} days."

        # Format events grouped by day
        formatted_events = []
        formatted_events.append(f"Events for the next {days_ahead} days:")
        formatted_events.append("")

        current_day = None
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')

            # Parse the time
            if 'T' in start:
                start_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                event_day = start_time.strftime('%A, %B %d, %Y')
                time_str = start_time.strftime('%I:%M %p')
            else:
                # All-day event
                start_time = datetime.datetime.fromisoformat(start)
                event_day = start_time.strftime('%A, %B %d, %Y')
                time_str = 'All Day'

            # Add day header if it's a new day
            if event_day != current_day:
                if current_day is not None:
                    formatted_events.append("")
                formatted_events.append(f"📆 {event_day}")
                current_day = event_day

            # Get optional fields
            location = event.get('location', '')

            # Format the event
            event_line = f"  • {time_str} - {summary}"
            if location:
                event_line += f" ({location})"

            formatted_events.append(event_line)

        print(f"Found {len(events)} event(s)")
        return "\n".join(formatted_events)

    except HttpError as error:
        error_msg = f"An error occurred: {error}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        return error_msg

if __name__ == "__main__":
    """Test the calendar functions."""
    print("=" * 60)
    print("Google Calendar Integration Test")
    print("=" * 60, "\n")

    # Test today's events
    print("Testing get_todays_events():")
    print("=" * 60)
    result = get_todays_event()
    print(result, "\n")

    print("=" * 60, "\n")

    # Test upcoming events
    print("Testing get_events_in_range(days_ahead=7):")
    print("=" * 60)
    result = get_events_in_range(days_ahead=7)
    print(result, "\n")

    print("=" * 60)