"""Google Calendar integration module for syncing Task and Case deadlines.

Supports both real Google Calendar (via OAuth2) and mock mode for testing.
Real credentials will be swapped in once founder provides OAuth client secret.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Will be set to True once credentials are available
CALENDAR_READY = False
calendar_service = None


def initialize_calendar_service():
    """Initialize Google Calendar service with OAuth2 credentials.
    
    Expects GOOGLE_CLIENT_SECRET_PATH env var pointing to credentials JSON file.
    Falls back to mock mode if credentials not available.
    """
    global CALENDAR_READY, calendar_service
    
    secret_path = os.environ.get('GOOGLE_CLIENT_SECRET_PATH')
    
    if not secret_path:
        logger.warning("GOOGLE_CLIENT_SECRET_PATH not set. Using mock calendar mode.")
        CALENDAR_READY = False
        return False
    
    if not os.path.exists(secret_path):
        logger.warning(f"Credentials file not found at {secret_path}. Using mock calendar mode.")
        CALENDAR_READY = False
        return False
    
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        
        scopes = ['https://www.googleapis.com/auth/calendar.events']
        creds = Credentials.from_service_account_file(secret_path, scopes=scopes)
        calendar_service = build('calendar', 'v3', credentials=creds)
        CALENDAR_READY = True
        logger.info("Google Calendar service initialized successfully")
        return True
    
    except ImportError:
        logger.warning("Google Calendar libraries not installed. Using mock mode.")
        CALENDAR_READY = False
        return False
    
    except Exception as e:
        logger.error(f"Failed to initialize Google Calendar: {str(e)}. Using mock mode.")
        CALENDAR_READY = False
        return False


def create_or_update_calendar_event(
    title: str,
    description: Optional[str],
    due_date: Optional[datetime],
    event_type: Optional[str] = None,
    location: Optional[str] = None,
    external_event_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create or update a Google Calendar event.
    
    Args:
        title: Event title
        description: Event description
        due_date: Event date/time
        event_type: Type of event (e.g., 'task_due', 'case_deadline')
        location: Event location
        external_event_id: Existing Google event ID to update (if any)
    
    Returns:
        {
            'success': bool,
            'event_id': str or None,  # Google Calendar event ID
            'error': str or None,
            'mock': bool  # True if using mock mode
        }
    """
    if not due_date:
        return {
            'success': False,
            'event_id': None,
            'error': 'due_date is required',
            'mock': not CALENDAR_READY
        }
    
    event_body = {
        'summary': title,
        'description': description or '',
        'start': {
            'dateTime': due_date.isoformat(),
            'timeZone': 'UTC'
        },
        'end': {
            'dateTime': due_date.isoformat(),
            'timeZone': 'UTC'
        }
    }
    
    if location:
        event_body['location'] = location
    
    if event_type:
        if 'description' in event_body:
            event_body['description'] += f"\n[Type: {event_type}]"
    
    # Mock mode: return success without actual Google Calendar call
    if not CALENDAR_READY:
        logger.debug(f"[MOCK] Calendar event: {title} on {due_date}")
        return {
            'success': True,
            'event_id': f"mock_{hash(title + str(due_date)) % 1000000}",
            'error': None,
            'mock': True
        }
    
    try:
        if external_event_id:
            # Update existing event
            result = calendar_service.events().update(
                calendarId='primary',
                eventId=external_event_id,
                body=event_body
            ).execute()
            logger.info(f"Updated calendar event: {result.get('id')}")
        else:
            # Create new event
            result = calendar_service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()
            logger.info(f"Created calendar event: {result.get('id')}")
        
        return {
            'success': True,
            'event_id': result.get('id'),
            'error': None,
            'mock': False
        }
    
    except Exception as e:
        logger.error(f"Failed to create/update calendar event: {str(e)}")
        return {
            'success': False,
            'event_id': None,
            'error': str(e),
            'mock': False
        }


def delete_calendar_event(external_event_id: str) -> Dict[str, Any]:
    """Delete a Google Calendar event.
    
    Args:
        external_event_id: Google Calendar event ID
    
    Returns:
        {'success': bool, 'error': str or None, 'mock': bool}
    """
    if not external_event_id:
        return {
            'success': False,
            'error': 'external_event_id is required',
            'mock': not CALENDAR_READY
        }
    
    # Mock mode
    if not CALENDAR_READY:
        logger.debug(f"[MOCK] Deleted calendar event: {external_event_id}")
        return {
            'success': True,
            'error': None,
            'mock': True
        }
    
    try:
        calendar_service.events().delete(
            calendarId='primary',
            eventId=external_event_id
        ).execute()
        logger.info(f"Deleted calendar event: {external_event_id}")
        return {
            'success': True,
            'error': None,
            'mock': False
        }
    
    except Exception as e:
        logger.error(f"Failed to delete calendar event: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'mock': False
        }


def get_calendar_event(external_event_id: str) -> Dict[str, Any]:
    """Fetch a Google Calendar event.
    
    Args:
        external_event_id: Google Calendar event ID
    
    Returns:
        {
            'success': bool,
            'event': dict or None,
            'error': str or None,
            'mock': bool
        }
    """
    if not external_event_id:
        return {
            'success': False,
            'event': None,
            'error': 'external_event_id is required',
            'mock': not CALENDAR_READY
        }
    
    # Mock mode
    if not CALENDAR_READY:
        return {
            'success': True,
            'event': None,  # Mock doesn't have real data
            'error': None,
            'mock': True
        }
    
    try:
        event = calendar_service.events().get(
            calendarId='primary',
            eventId=external_event_id
        ).execute()
        return {
            'success': True,
            'event': event,
            'error': None,
            'mock': False
        }
    
    except Exception as e:
        logger.error(f"Failed to fetch calendar event: {str(e)}")
        return {
            'success': False,
            'event': None,
            'error': str(e),
            'mock': False
        }


# Initialize on module load
initialize_calendar_service()
