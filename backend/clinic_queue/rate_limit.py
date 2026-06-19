"""Rate limiting utilities to prevent abuse of queue operations."""

from django.utils import timezone
from datetime import timedelta


def rate_limit_key(action, user_id):
    """Generate a cache key for rate limiting."""
    return f"rate_limit:{action}:{user_id}"


def check_rate_limit(request, action, max_per_minute=60, seconds_between=0):
    """
    Check if user has exceeded rate limit for an action.
    
    Returns:
        (is_limited: bool, remaining_wait_seconds: int)
    """
    from django.core.cache import cache
    
    if not request.user.is_authenticated:
        return False, 0
    
    key = rate_limit_key(action, request.user.id)
    
    # If seconds_between is set, enforce minimum time between actions
    if seconds_between > 0:
        last_action = cache.get(key)
        if last_action:
            elapsed = (timezone.now() - last_action).total_seconds()
            if elapsed < seconds_between:
                remaining = seconds_between - int(elapsed)
                return True, remaining
    
    # Record this action
    cache.set(key, timezone.now(), timeout=60)
    return False, 0


def get_rate_limit_context(request):
    """Get context about current rate limit status."""
    return {
        'rate_limit_enabled': True,
        'rate_limit_call_next': 2,  # 2 seconds between calls
        'rate_limit_create_token': 1,  # 1 second between creates
    }
