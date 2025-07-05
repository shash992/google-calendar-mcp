# Additional tools for calendar search, listing, free/busy, and recurring events
from typing import List, Optional

import os
from fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
mcp = FastMCP("Google Calendar MCP")

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

@mcp.tool
def list_calendar_events(calendar_id: str = None, time_min: str = None, time_max: str = None):
    """List events from a calendar between optional time_min and time_max."""
    service = get_calendar_service()

    # Fallback to 'primary' if no calendar_id provided
    if not calendar_id:
        calendar_id = 'primary'

    try:
        events = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events.get('items', [])
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "calendar_id": calendar_id
        }

@mcp.tool
def create_calendar_event(calendar_id: str, summary: str, start: str, end: str, attendees: list = None, description: str = None, location: str = None):
    """Create a calendar event with optional attendees, description, and location."""
    service = get_calendar_service()
    event = {
        'summary': summary,
        'start': {'dateTime': start},
        'end': {'dateTime': end},
        **({'attendees': [{'email': email} for email in attendees]} if attendees else {}),
        **({'description': description} if description else {}),
        **({'location': location} if location else {})
    }
    created = service.events().insert(calendarId=calendar_id, body=event).execute()
    return created


@mcp.tool
def delete_calendar_event(calendar_id: str, event_id: str):
    """Delete a calendar event by its ID."""
    service = get_calendar_service()
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"status": "success", "message": f"Event {event_id} deleted."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool
def update_calendar_event(calendar_id: str, event_id: str, summary: str = None, start: str = None, end: str = None, attendees: list = None, description: str = None, location: str = None):
    """Update a calendar event with optional new details."""
    service = get_calendar_service()
    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        if summary is not None:
            event['summary'] = summary
        if start is not None:
            event['start'] = {'dateTime': start}
        if end is not None:
            event['end'] = {'dateTime': end}
        if attendees is not None:
            event['attendees'] = [{'email': email} for email in attendees]
        if description is not None:
            event['description'] = description
        if location is not None:
            event['location'] = location
        updated_event = service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
        return updated_event
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Do not call mcp.run() explicitly, since fastmcp will handle it via CLI entry


@mcp.tool
def reauthenticate_user():
    """Delete the current authentication token and trigger OAuth flow again to allow re-authentication and account switching."""
    token_path = 'token.json'
    if os.path.exists(token_path):
        os.remove(token_path)
        # Next call to get_calendar_service() will trigger OAuth flow
        return {"status": "success", "message": "Token deleted. Please authenticate again to reauthorize or switch accounts."}
    else:
        return {"status": "info", "message": "No token found. Next operation will trigger OAuth flow."}
# 1. Search calendar events by keyword
@mcp.tool
def search_calendar_events(calendar_id: str = 'primary', query: str = '', time_min: str = None, time_max: str = None):
    """Search for events in a calendar by keyword (query)."""
    service = get_calendar_service()
    events_result = service.events().list(
        calendarId=calendar_id,
        q=query,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

# 2. List all accessible calendars
@mcp.tool
def list_user_calendars():
    """List all calendars accessible by the user."""
    service = get_calendar_service()
    calendar_list = service.calendarList().list().execute()
    return calendar_list.get('items', [])


# 3. Get free/busy information for all user calendars
@mcp.tool
def get_free_busy_all(time_min: str, time_max: str):
    """
    Return busy times for all user-accessible calendars between time_min and time_max (RFC3339 format).
    Returns a dict mapping calendar IDs to their busy periods.
    """
    service = get_calendar_service()
    if not time_min or not time_max:
        return {"status": "error", "message": "time_min and time_max (RFC3339) are required."}
    # Get all user calendars
    calendars = service.calendarList().list().execute().get("items", [])
    items = [{"id": cal["id"]} for cal in calendars]
    if not items:
        return {"status": "error", "message": "No calendars found for user."}
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": items
    }
    freebusy_result = service.freebusy().query(body=body).execute()
    result = {}
    for cal_id, cal_info in freebusy_result.get("calendars", {}).items():
        result[cal_id] = cal_info.get("busy", [])
    return result

# 4. Create a recurring event using RRULE
@mcp.tool
def create_recurring_event(
    calendar_id: str,
    summary: str,
    start: str,
    end: str,
    rrule: str,
    attendees: Optional[List[str]] = None,
    description: str = None,
    location: str = None
):
    """
    Create a recurring calendar event using an RRULE string.
    Example RRULE: "RRULE:FREQ=WEEKLY;COUNT=10"
    """
    service = get_calendar_service()
    event = {
        'summary': summary,
        'start': {'dateTime': start},
        'end': {'dateTime': end},
        'recurrence': [rrule],
        **({'attendees': [{'email': email} for email in attendees]} if attendees else {}),
        **({'description': description} if description else {}),
        **({'location': location} if location else {})
    }
    created = service.events().insert(calendarId=calendar_id, body=event).execute()
    return created