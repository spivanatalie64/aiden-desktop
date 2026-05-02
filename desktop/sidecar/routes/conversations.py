"""Conversations routes – list, read, delete encrypted conversations."""
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aiden_storage import (
    list_conversations, decrypt_conversation, encrypt_and_store,
    new_conversation_id,
)
from settings import load_settings

router = APIRouter(prefix="/conversations", tags=["conversations"])


class SaveRequest(BaseModel):
    text: str
    password: str
    conversation_id: Optional[str] = None


class DecryptRequest(BaseModel):
    conversation_id: str
    password: str


@router.get("")
async def list_all():
    settings = load_settings()
    base = Path(settings.get("storage_dir", str(Path.home() / ".local" / "share" / "aiden")))
    convos = list_conversations(base)
    return {"conversations": convos}


@router.post("/decrypt")
async def decrypt(req: DecryptRequest):
    settings = load_settings()
    base = Path(settings.get("storage_dir", str(Path.home() / ".local" / "share" / "aiden")))
    try:
        text = decrypt_conversation(req.conversation_id, req.password, base)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {e}")


@router.post("/save")
async def save(req: SaveRequest):
    settings = load_settings()
    base = Path(settings.get("storage_dir", str(Path.home() / ".local" / "share" / "aiden")))
    try:
        cid = encrypt_and_store(
            req.text, req.password,
            convo_id=req.conversation_id,
            base=base,
        )
        return {"conversation_id": cid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Save failed: {e}")
