import json
import os
import sys

_DEFAULTS = {
    "top_n":          10,
    "bar_width":      40,
    "log_glob":       "/var/log/fail2ban.log*",
    "attempted_file": "data/attempted.txt",
    "cache_file":     "data/cache.json",
    "verbose":        False,
    "char_filled":    "·",
    "char_empty":     "·",
}

# settings.json lives in data/, two levels up from this file (scripts/settings.py)
_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "settings.json")


def load() -> dict:
    if not os.path.exists(_FILE):
        print(f"[Error] settings.json not found at {_FILE}")
        sys.exit(1)
    with open(_FILE) as f:
        data = json.load(f)
    cfg = {**_DEFAULTS, **data}
    if not cfg.get("api_token") or cfg["api_token"] == "your_token_here":
        print("[Error] Set your api_token in data/settings.json")
        sys.exit(1)
    return cfg
