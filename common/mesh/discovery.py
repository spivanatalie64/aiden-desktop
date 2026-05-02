import json
import socket
import struct
import hashlib
import threading
import time
from pathlib import Path
from typing import Optional, Callable

from common.crypto import (
    NodeIdentity, ecdh_handshake, encrypt_message, decrypt_message,
    sign_challenge, verify_challenge,
)
from common.audit import emit_mesh

PEER_STORE_PATH = Path.home() / '.config' / 'aiden' / 'peers.json'
ACCEPTED_PEERS_PATH = Path.home() / '.config' / 'aiden' / 'accepted_peers.json'
BLOCKED_PEERS_PATH = Path.home() / '.config' / 'aiden' / 'blocked_peers.json'

PEER_PORT = 19090
MULTICAST_ADDR = '224.0.0.251'
MULTICAST_PORT = 19091


class PeerInfo:
    def __init__(self, node_id: str, hostname: str, fingerprint: str,
                 pubkey_raw: bytes, addr: str = '', port: int = PEER_PORT):
        self.node_id = node_id
        self.hostname = hostname
        self.fingerprint = fingerprint
        self.pubkey_raw = pubkey_raw
        self.addr = addr
        self.port = port
        self.session_key: Optional[bytes] = None
        self.seq = 0
        self.last_seen: float = time.time()
        self.accepted: bool = False


class PeerDiscovery:
    def __init__(self, identity: NodeIdentity, hostname: str):
        self.identity = identity
        self.hostname = hostname
        self.peers: dict[str, PeerInfo] = {}
        self._listeners: list[Callable] = []
        self._running = False
        self._load_accepted()

    def on_peer_found(self, callback: Callable):
        self._listeners.append(callback)

    def start(self):
        self._running = True
        threading.Thread(target=self._announce_loop, daemon=True).start()
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def stop(self):
        self._running = False

    def get_peers(self) -> list[PeerInfo]:
        return list(self.peers.values())

    def accept_peer(self, fingerprint: str) -> bool:
        peer = self.peers.get(fingerprint)
        if not peer:
            return False
        peer.accepted = True
        accepted = self._load_json(ACCEPTED_PEERS_PATH)
        if fingerprint not in accepted:
            accepted.append({
                'fingerprint': fingerprint,
                'pubkey_raw': peer.pubkey_raw.hex(),
                'hostname': peer.hostname,
                'accepted_at': time.time(),
            })
            self._save_json(ACCEPTED_PEERS_PATH, accepted)
        return True

    def reject_peer(self, fingerprint: str) -> bool:
        peer = self.peers.get(fingerprint)
        if not peer:
            return False
        blocked = self._load_json(BLOCKED_PEERS_PATH)
        if fingerprint not in blocked:
            blocked.append(fingerprint)
            self._save_json(BLOCKED_PEERS_PATH, blocked)
        self.peers.pop(fingerprint, None)
        return True

    def _announce_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        while self._running:
            ann = json.dumps({
                'type': 'aiden-announce',
                'node_id': self.identity.fingerprint,
                'hostname': self.hostname,
                'fingerprint': self.identity.full_fingerprint,
                'pubkey': self.identity.public_key_bytes().hex(),
                'port': PEER_PORT,
            })
            try:
                sock.sendto(ann.encode(), (MULTICAST_ADDR, MULTICAST_PORT))
            except OSError:
                pass
            time.sleep(30)

    def _listen_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('', MULTICAST_PORT))
            mreq = struct.pack(
                '4sl', socket.inet_aton(MULTICAST_ADDR), socket.INADDR_ANY
            )
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.settimeout(5)
        except OSError:
            return

        while self._running:
            try:
                data, addr = sock.recvfrom(4096)
                msg = json.loads(data.decode())
                if msg.get('type') != 'aiden-announce':
                    continue
                if msg['node_id'] == self.identity.fingerprint:
                    continue
                fp = msg['fingerprint']
                blocked = self._load_json(BLOCKED_PEERS_PATH)
                if fp in blocked:
                    continue
                if fp not in self.peers:
                    pubkey = bytes.fromhex(msg['pubkey'])
                    peer = PeerInfo(
                        node_id=msg['node_id'],
                        hostname=msg['hostname'],
                        fingerprint=fp,
                        pubkey_raw=pubkey,
                        addr=addr[0],
                        port=msg.get('port', PEER_PORT),
                    )
                    accepted = self._load_json(ACCEPTED_PEERS_PATH)
                    for a in accepted:
                        if a['fingerprint'] == fp:
                            peer.accepted = True
                            break
                    self.peers[fp] = peer
                    for cb in self._listeners:
                        cb(peer)
                else:
                    self.peers[fp].last_seen = time.time()
            except (socket.timeout, json.JSONDecodeError):
                continue

    def _load_accepted(self):
        accepted = self._load_json(ACCEPTED_PEERS_PATH)
        for a in accepted:
            fp = a['fingerprint']
            if fp not in self.peers:
                pubkey = bytes.fromhex(a['pubkey_raw'])
                peer = PeerInfo(
                    node_id=fp[:16],
                    hostname=a.get('hostname', 'unknown'),
                    fingerprint=fp,
                    pubkey_raw=pubkey,
                )
                peer.accepted = True
                self.peers[fp] = peer

    @staticmethod
    def _load_json(path: Path) -> list:
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text())
        except Exception:
            return []

    @staticmethod
    def _save_json(path: Path, data: list):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
