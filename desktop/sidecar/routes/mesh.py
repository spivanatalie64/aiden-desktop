"""Mesh routes – LAN peer discovery and cache sharing."""
import json
import hashlib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from common.mesh.discovery import PeerDiscovery, PeerInfo, PEER_PORT
from common.mesh.session import DistributedCache, cache_key
from common.audit import emit_mesh
from common.crypto import NodeIdentity
from settings import load_settings, save_settings

router = APIRouter(prefix="/mesh", tags=["mesh"])

_cache = DistributedCache()
_discovery: Optional[PeerDiscovery] = None


def get_discovery() -> PeerDiscovery:
    global _discovery
    if _discovery is None:
        settings = load_settings()
        from common.crypto import load_key_from_agent, load_key_from_file
        import os, socket

        identity = load_key_from_agent()
        if identity is None:
            key_path = settings.get("ssh_key_path", "")
            if key_path and os.path.exists(key_path):
                identity = load_key_from_file(key_path)
        if identity is None:
            raise RuntimeError("No SSH identity available for mesh")

        _discovery = PeerDiscovery(identity, socket.gethostname())
        _discovery.start()
    return _discovery


@router.get("/peers")
async def list_peers():
    try:
        discovery = get_discovery()
    except RuntimeError:
        return {"peers": [], "error": "No SSH identity configured"}
    peers = []
    for p in discovery.get_peers():
        peers.append({
            "node_id": p.node_id,
            "hostname": p.hostname,
            "fingerprint": p.fingerprint,
            "addr": p.addr,
            "port": p.port,
            "last_seen": p.last_seen,
            "accepted": p.accepted,
        })
    return {"peers": peers}


@router.post("/peers/accept")
async def accept_peer(body: dict):
    fingerprint = body.get("fingerprint", "")
    if not fingerprint:
        raise HTTPException(status_code=400, detail="fingerprint required")
    try:
        discovery = get_discovery()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if discovery.accept_peer(fingerprint):
        emit_mesh("system", "accept", fingerprint, "success")
        return {"status": "accepted"}
    raise HTTPException(status_code=404, detail="Peer not found")


@router.post("/peers/reject")
async def reject_peer(body: dict):
    fingerprint = body.get("fingerprint", "")
    if not fingerprint:
        raise HTTPException(status_code=400, detail="fingerprint required")
    try:
        discovery = get_discovery()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if discovery.reject_peer(fingerprint):
        emit_mesh("system", "reject", fingerprint, "blocked")
        return {"status": "rejected"}
    raise HTTPException(status_code=404, detail="Peer not found")


@router.get("/cache/status")
async def cache_status():
    return {
        "entries": _cache.size(),
        "keys": _cache.keys(),
    }


class CacheGetRequest(BaseModel):
    prompt: str
    model: str
    system_prompt: str = ""
    temperature: float = 0.7


@router.post("/cache/get")
async def cache_get(req: CacheGetRequest):
    key = cache_key(req.prompt, req.model, req.system_prompt, req.temperature)
    entry = _cache.get(key)
    if entry:
        return {"hit": True, "reply": entry.reply, "source": entry.source_node}
    return {"hit": False}


class CacheAnnounceRequest(BaseModel):
    prompt: str
    model: str
    system_prompt: str = ""
    temperature: float = 0.7
    reply: str


@router.post("/cache/announce")
async def cache_announce(req: CacheAnnounceRequest):
    key = cache_key(req.prompt, req.model, req.system_prompt, req.temperature)
    from common.mesh.session import CacheEntry
    entry = CacheEntry(
        key_hash=key,
        reply=req.reply,
        model=req.model,
        source_node="local",
    )
    _cache.set(entry)
    return {"status": "cached", "key": key}


@router.get("/discovery/status")
async def discovery_status():
    try:
        d = get_discovery()
        return {"running": True, "peers_count": len(d.get_peers())}
    except RuntimeError:
        return {"running": False, "error": "No SSH identity"}
