"""Webhook dispatcher — fire-and-forget HTTP POST to a configured URL.

Configured via WEBHOOK_URL env var. When set, every call to fire() attempts
to deliver the payload. In mock mode (no URL configured), it just logs.

Use this for external integrations (Zapier, n8n, custom listeners) when real
notifiers (email, calendar, etc.) aren't available yet.
"""

import os
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '').strip() or None


def fire(event: str, payload: Dict[str, Any], url: Optional[str] = None) -> Dict[str, Any]:
    """Send a webhook POST with the event payload.
    
    Args:
        event: event tag (e.g. 'task.created', 'task.completed', 'user.invited')
        payload: JSON-serializable dict of the event's data
        url: optional override (for tests / per-call customization)
    
    Returns:
        {
            'success': bool,
            'mock': bool,           # True if no URL configured (logged only)
            'status_code': int,     # None if mock
            'error': str or None,
        }
    """
    target = url or WEBHOOK_URL
    
    if not target:
        logger.debug(f"[MOCK WEBHOOK] event={event} payload={payload}")
        return {'success': True, 'mock': True, 'status_code': None, 'error': None}
    
    envelope = {
        'event': event,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'payload': payload,
    }
    
    try:
        import requests
    except ImportError:
        return {
            'success': False,
            'mock': True,
            'status_code': None,
            'error': 'requests library not installed',
        }
    
    try:
        resp = requests.post(
            target,
            json=envelope,
            headers={'Content-Type': 'application/json', 'X-Event': event},
            timeout=5
        )
        ok = 200 <= resp.status_code < 300
        if not ok:
            logger.warning(f"Webhook non-2xx: {resp.status_code} for event={event}")
        return {
            'success': ok,
            'mock': False,
            'status_code': resp.status_code,
            'error': None if ok else resp.text[:200],
        }
    except Exception as e:
        logger.error(f"Webhook POST failed: {e}")
        return {
            'success': False,
            'mock': False,
            'status_code': None,
            'error': str(e),
        }


# Convenience wrappers (match notification types for symmetry)
def task_created(task_dict: Dict[str, Any], actor_id: Optional[int] = None) -> Dict:
    return fire('task.created', {'task': task_dict, 'actor_id': actor_id})

def task_updated(task_dict: Dict[str, Any], actor_id: Optional[int] = None, fields_changed: Optional[list] = None) -> Dict:
    return fire('task.updated', {'task': task_dict, 'actor_id': actor_id, 'fields_changed': fields_changed or []})

def task_completed(task_dict: Dict[str, Any], actor_id: Optional[int] = None) -> Dict:
    return fire('task.completed', {'task': task_dict, 'actor_id': actor_id})

def task_deleted(task_id: int, actor_id: Optional[int] = None) -> Dict:
    return fire('task.deleted', {'task_id': task_id, 'actor_id': actor_id})
