"""Settings routes – CRUD for app configuration, presets, providers, disclaimer."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from settings import (
    load_settings, save_settings, is_disclaimer_accepted, accept_disclaimer,
    get_active_preset, set_active_preset, get_presets, save_preset,
    get_providers, add_provider, remove_provider, get_code_exec_mode,
    set_code_exec_mode, DEFAULT_SETTINGS,
)
from common.presets import PRESETS, list_presets
from common.audit import emit_settings_change

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_all_settings():
    s = load_settings()
    safe = {k: v for k, v in s.items()
            if k not in ("ssh_key_path",)}
    return safe


@router.put("")
async def update_settings(body: dict):
    s = load_settings()
    for k, v in body.items():
        if k in s:
            s[k] = v
    save_settings(s)
    return {"status": "ok"}


@router.get("/disclaimer")
async def check_disclaimer():
    return {"accepted": is_disclaimer_accepted()}


@router.post("/disclaimer")
async def accept():
    accept_disclaimer()
    return {"accepted": True}


@router.get("/presets")
async def list_all_presets():
    return get_presets()


@router.get("/presets/active")
async def active_preset():
    preset = get_active_preset()
    key = load_settings().get("active_preset", "default")
    return {"key": key, **preset}


@router.put("/presets/active")
async def set_active(key: str):
    set_active_preset(key)
    return {"key": key}


@router.put("/presets/{key}")
async def update_preset(key: str, body: dict):
    presets = get_presets()
    if key not in presets:
        raise HTTPException(status_code=404, detail=f"Preset not found: {key}")
    presets[key].update(body)
    save_preset(key, presets[key])
    return {"status": "ok"}


@router.get("/providers")
async def list_providers():
    return {"providers": get_providers()}


@router.post("/providers")
async def create_provider(body: dict):
    name = body.get("name", "")
    url = body.get("base_url", "")
    key = body.get("api_key", "")
    if not name or not url:
        raise HTTPException(status_code=400, detail="name and base_url required")
    add_provider(name, url, key)
    return {"status": "ok"}


@router.delete("/providers/{name}")
async def delete_provider(name: str):
    remove_provider(name)
    return {"status": "ok"}


@router.get("/code-exec-mode")
async def exec_mode():
    return {"mode": get_code_exec_mode()}


@router.put("/code-exec-mode")
async def update_exec_mode(body: dict):
    mode = body.get("mode", "click_to_run")
    valid = ["click_to_run", "trust_conversation", "auto_run_safe", "auto_run_all"]
    if mode not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
    set_code_exec_mode(mode)
    return {"mode": mode}
