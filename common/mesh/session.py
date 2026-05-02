import asyncio
import json
import hashlib
import time
from typing import Optional

from common.crypto import (
    NodeIdentity, ecdh_handshake, encrypt_message, decrypt_message,
    sign_challenge, verify_challenge,
)
from common.mesh.discovery import PeerInfo


class PeerSession:
    def __init__(self, identity: NodeIdentity, peer: PeerInfo):
        self.identity = identity
        self.peer = peer
        self.session_key: Optional[bytes] = None
        self.seq = 0

    async def handshake(self) -> bool:
        challenge = hashlib.sha256(b'aiden-handshake').digest()
        sig = sign_challenge(self.identity, challenge)
        peer_pub = self.peer.pubkey_raw

        if not verify_challenge(peer_pub, challenge, sig):
            return False

        session_key, our_eph = ecdh_handshake(self.identity, peer_pub)
        self.session_key = session_key
        return True

    def encrypt(self, plaintext: bytes) -> bytes:
        self.seq += 1
        return encrypt_message(self.session_key, plaintext, self.seq)

    def decrypt(self, data: bytes) -> bytes:
        return decrypt_message(self.session_key, data)


class CacheEntry:
    def __init__(self, key_hash: str, reply: str, model: str,
                 source_node: str, ttl: int = 3600):
        self.key_hash = key_hash
        self.reply = reply
        self.model = model
        self.source_node = source_node
        self.expires = time.time() + ttl


class DistributedCache:
    def __init__(self):
        self._entries: dict[str, CacheEntry] = {}

    def get(self, key_hash: str) -> Optional[CacheEntry]:
        entry = self._entries.get(key_hash)
        if not entry:
            return None
        if time.time() > entry.expires:
            del self._entries[key_hash]
            return None
        return entry

    def set(self, entry: CacheEntry):
        self._entries[entry.key_hash] = entry

    def invalidate(self, key_hash: str):
        self._entries.pop(key_hash, None)

    def size(self) -> int:
        return len(self._entries)

    def keys(self) -> list[str]:
        return list(self._entries.keys())


def cache_key(prompt: str, model: str, system_prompt: str,
              temperature: float) -> str:
    raw = json.dumps({
        'prompt': prompt,
        'model': model,
        'system_prompt': system_prompt,
        'temperature': temperature,
    }, sort_keys=True).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()
