"""
Security utilities for EvacuaLink:
- Client IP resolution
- Rate limiting and brute force protection via Django cache
"""

from django.core.cache import cache
import hashlib


def get_client_ip(request):
    """
    Safely extract client IP from request headers, accounting for proxies.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # First IP in the list is the original client IP
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
    return ip


def get_rate_limit_key(prefix, identifier):
    """
    Create a sanitized, hashed key for rate-limiting cache entries.
    """
    hashed = hashlib.sha256(str(identifier).lower().encode("utf-8")).hexdigest()[:32]
    return f"ratelimit:{prefix}:{hashed}"


def get_failed_attempts(key):
    """
    Retrieve current number of recorded failures for a key.
    """
    try:
        return cache.get(key, 0)
    except Exception:
        return 0


def record_failed_attempt(key, timeout=300):
    """
    Increment failed attempt count with an expiry window (default: 5 minutes).
    """
    try:
        current = cache.get(key, 0)
        cache.set(key, current + 1, timeout=timeout)
        return current + 1
    except Exception:
        return 1


def reset_failed_attempts(key):
    """
    Reset failed attempts for a key upon successful authentication.
    """
    try:
        cache.delete(key)
    except Exception:
        pass


def is_rate_limited(key, max_attempts=5):
    """
    Check if a key has reached or exceeded max permitted attempts.
    """
    return get_failed_attempts(key) >= max_attempts
