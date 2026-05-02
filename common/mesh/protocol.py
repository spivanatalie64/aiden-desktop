import struct
from typing import Tuple

from common.crypto import encrypt_message, decrypt_message

PROTOCOL_VERSION = 1

MESSAGE_TYPES = {
    'CACHE_GET': 0x01,
    'CACHE_HIT': 0x02,
    'CACHE_MISS': 0x03,
    'CACHE_ANNOUNCE': 0x04,
    'PEER_ACCEPT': 0x10,
    'PEER_REJECT': 0x11,
    'PEER_ACCEPT_BACK': 0x12,
    'HEARTBEAT': 0xFF,
}

TYPE_NAMES = {v: k for k, v in MESSAGE_TYPES.items()}


def encode_message(msg_type: int, payload: bytes, key: bytes, seq: int) -> bytes:
    header = struct.pack('>BHI', PROTOCOL_VERSION, msg_type, seq)
    encrypted = encrypt_message(key, header + payload, seq)
    return struct.pack('>I', len(encrypted)) + encrypted


def decode_message(data: bytes, key: bytes) -> Tuple[int, bytes, int]:
    length = struct.unpack('>I', data[:4])[0]
    pt, seq = decrypt_message(key, data[4:4+length])
    version, msg_type, orig_seq = struct.unpack('>BHI', pt[:7])
    return msg_type, pt[7:], seq


def build_cache_get(key_hash: str) -> bytes:
    return key_hash.encode('ascii')


def build_cache_hit(key_hash: str, reply: str, source: str) -> bytes:
    payload = f'{key_hash}\n{source}\n'.encode('utf-8') + reply.encode('utf-8')
    return payload


def build_cache_miss(key_hash: str) -> bytes:
    return key_hash.encode('ascii')


def parse_cache_hit(data: bytes) -> Tuple[str, str, str]:
    parts = data.split(b'\n', 2)
    key_hash = parts[0].decode('ascii')
    source = parts[1].decode('ascii')
    reply = parts[2].decode('utf-8') if len(parts) > 2 else ''
    return key_hash, reply, source
