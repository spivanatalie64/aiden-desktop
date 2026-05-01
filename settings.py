import json
from pathlib import Path

DEFAULT_DIR = Path.home() / '.local' / 'share' / 'aiden'
DEFAULT_SETTINGS = {
    'proxy_url': 'https://aiden.acreetionos.org/api/chat',
    'storage_dir': str(DEFAULT_DIR),
    'helper_path': '/usr/libexec/aiden-helper.py',
    'model_whitelist': [],
    'snippet_max_chars': 800,
}


def settings_path() -> Path:
    cfg_dir = Path.home() / '.config' / 'aiden'
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / 'settings.json'


def load_settings() -> dict:
    p = settings_path()
    if not p.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = DEFAULT_SETTINGS.copy()
    # Ensure defaults present
    for k, v in DEFAULT_SETTINGS.items():
        if k not in data:
            data[k] = v
    return data


def save_settings(d: dict):
    p = settings_path()
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2)
