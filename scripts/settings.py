import json
import os
import sys
import logging

logger = logging.getLogger("fail2ban-intel")

_DEFAULTS: dict = {
    "top_n":          10,
    "bar_width":      40,
    "log_glob":       "/var/log/fail2ban.log*",
    "attempted_file": "data/attempted.txt",
    "cache_file":     "data/cache.json",
    "cache_ttl_days": 30,
    "verbose":        False,
    "minimal":        False,
    "char_filled":    "·",
    "char_empty":     "·",
    "retry_count":    3,
    "retry_delay":    1.0,
}

_EXPECTED_TYPES: dict[str, type | tuple[type, ...]] = {
    "top_n":          int,
    "bar_width":      int,
    "log_glob":       str,
    "attempted_file": str,
    "cache_file":     str,
    "cache_ttl_days": int,
    "verbose":        bool,
    "minimal":        bool,
    "char_filled":    str,
    "char_empty":     str,
    "retry_count":    int,
    "retry_delay":    (int, float),
}

_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "settings.json")


def _validate(cfg: dict) -> None:
    for key, expected in _EXPECTED_TYPES.items():
        if key not in cfg:
            continue
        val = cfg[key]
        if not isinstance(val, expected):
            logger.warning(
                "settings.json: %s should be %s, got %s (%s) — using default",
                key, expected, type(val).__name__, repr(val),
            )
            cfg[key] = _DEFAULTS[key]


def load() -> dict:
    if not os.path.exists(_FILE):
        logger.error("settings.json not found at %s", _FILE)
        sys.exit(1)

    try:
        with open(_FILE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to read settings.json: %s", e)
        sys.exit(1)

    cfg = {**_DEFAULTS, **data}
    _validate(cfg)

    if not cfg.get("api_token") or cfg["api_token"] == "your_token_here":
        logger.error("Set your api_token in data/settings.json")
        sys.exit(1)

    return cfg
