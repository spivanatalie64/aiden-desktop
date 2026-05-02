import json
from pathlib import Path
from typing import Optional

from common.presets import PRESETS

DEFAULT_DIR = Path.home() / '.local' / 'share' / 'aiden'
CONFIG_DIR = Path.home() / '.config' / 'aiden'

DEFAULT_SETTINGS = {
    'proxy_url': 'https://aiden.acreetionos.org/api/chat',
    'storage_dir': str(DEFAULT_DIR),
    'helper_path': '/usr/libexec/aiden-helper.py',
    'model_whitelist': [],
    'snippet_max_chars': 800,
    'disclaimer_accepted': False,
    'active_preset': 'default',
    'presets': {k: v for k, v in PRESETS.items()},
    'mesh_enabled': False,
    'mesh_port': 19090,
    'ssh_key_path': '',
    'accepted_peers': [],
    'blocked_peers': [],
    'code_exec_mode': 'click_to_run',
    'code_exec_timeout': 30,
    'providers': [
        {
            'name': 'AIDEN Proxy',
            'base_url': 'https://aiden.acreetionos.org/api/chat',
            'api_key': '',
            'enabled': True,
        }
    ],
    'language': 'en',
    'theme': 'dark',
    'reasoning_effort': 'auto',
    'temperature': 0.7,
    'max_tokens': 4096,
}


def settings_path() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR / 'settings.json'


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
    for k, v in DEFAULT_SETTINGS.items():
        if k not in data:
            data[k] = v
    if 'presets' not in data or not data['presets']:
        data['presets'] = {k: v for k, v in PRESETS.items()}
    return data


def save_settings(d: dict):
    p = settings_path()
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2)


def is_disclaimer_accepted() -> bool:
    return load_settings().get('disclaimer_accepted', False)


def accept_disclaimer():
    s = load_settings()
    s['disclaimer_accepted'] = True
    save_settings(s)


def get_active_preset() -> dict:
    s = load_settings()
    key = s.get('active_preset', 'default')
    presets = s.get('presets', {})
    return presets.get(key, PRESETS.get('default', {}))


def set_active_preset(key: str):
    s = load_settings()
    presets = s.get('presets', {})
    if key in presets:
        s['active_preset'] = key
        save_settings(s)


def get_presets() -> dict:
    s = load_settings()
    presets = s.get('presets', {})
    if not presets:
        presets = {k: v for k, v in PRESETS.items()}
        s['presets'] = presets
        save_settings(s)
    return presets


def save_preset(key: str, preset: dict):
    s = load_settings()
    s.setdefault('presets', {})[key] = preset
    save_settings(s)


def get_providers() -> list:
    s = load_settings()
    return s.get('providers', DEFAULT_SETTINGS['providers'])


def add_provider(name: str, base_url: str, api_key: str = ''):
    s = load_settings()
    s.setdefault('providers', []).append({
        'name': name,
        'base_url': base_url,
        'api_key': api_key,
        'enabled': True,
    })
    save_settings(s)


def remove_provider(name: str):
    s = load_settings()
    s['providers'] = [p for p in s.get('providers', []) if p['name'] != name]
    save_settings(s)


def get_code_exec_mode() -> str:
    return load_settings().get('code_exec_mode', 'click_to_run')


def set_code_exec_mode(mode: str):
    s = load_settings()
    s['code_exec_mode'] = mode
    save_settings(s)
