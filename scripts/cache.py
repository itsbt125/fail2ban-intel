import json
import os
import time
import logging

logger = logging.getLogger("fail2ban-intel")


def load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Corrupted cache file %s: %s — starting fresh", path, e)
        return {}


def save(path: str, cache: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(cache, f, indent=2)


def prune(cache: dict, ttl_days: int) -> tuple[int, int]:
    if ttl_days <= 0:
        return 0, len(cache)
    now = time.time()
    cutoff = now - (ttl_days * 86400)
    before = len(cache)
    stale = [ip for ip, entry in cache.items()
              if isinstance(entry, dict) and entry.get("_cached_at", 0) < cutoff]
    for ip in stale:
        del cache[ip]
    removed = len(stale)
    if removed:
        logger.info("Pruned %d expired cache entries (TTL=%d days)", removed, ttl_days)
    return removed, before
