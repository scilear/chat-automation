import json
from pathlib import Path
CACHE_FILE = Path.home() / ".chat_automation" / "perplexity_spaces_cache.json"


def save_spaces_cache(spaces):
    with open(CACHE_FILE, "w") as f:
        json.dump([space.__dict__ for space in spaces], f)


def load_spaces_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        return data
    except Exception:
        return []
