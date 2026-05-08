import time

_cache = {}

def get_cached(key: str, ttl_seconds: int = 1800):
    if key in _cache:
        data, timestamp = _cache[key]
        if time.time() - timestamp < ttl_seconds:
            return data
    return None

def set_cache(key: str, data):
    _cache[key] = (data, time.time())

def clear_cache(key: str = None):
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()