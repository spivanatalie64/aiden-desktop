"""Tests for common/mesh/protocol.py – wire format encoding/decoding."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

from common.mesh.protocol import (
    encode_message, decode_message,
    build_cache_get, build_cache_hit, build_cache_miss,
    parse_cache_hit,
    MESSAGE_TYPES,
)


TEST_KEY = os.urandom(32)


class TestProtocolEncoding:
    def test_encode_decode_roundtrip(self):
        for msg_type in [MESSAGE_TYPES['CACHE_GET'],
                         MESSAGE_TYPES['CACHE_HIT'],
                         MESSAGE_TYPES['CACHE_MISS'],
                         MESSAGE_TYPES['HEARTBEAT']]:
            payload = b'test payload data'
            for seq in (1, 42, 65535):
                encoded = encode_message(msg_type, payload, TEST_KEY, seq)
                decoded_type, decoded_payload, decoded_seq = decode_message(encoded, TEST_KEY)
                assert decoded_type == msg_type
                assert decoded_payload == payload
                assert decoded_seq == seq

    def test_encode_decode_rejects_wrong_key(self):
        wrong_key = os.urandom(32)
        encoded = encode_message(MESSAGE_TYPES['CACHE_GET'], b'data', TEST_KEY, 1)
        with pytest.raises(Exception):
            decode_message(encoded, wrong_key)

    def test_encode_decode_rejects_tampered(self):
        encoded = encode_message(MESSAGE_TYPES['CACHE_GET'], b'data', TEST_KEY, 1)
        tampered = bytearray(encoded)
        tampered[-1] ^= 0xFF
        with pytest.raises(Exception):
            decode_message(bytes(tampered), TEST_KEY)


class TestCacheMessages:
    def test_build_cache_get(self):
        key_hash = 'a' * 64
        data = build_cache_get(key_hash)
        assert data == key_hash.encode('ascii')

    def test_build_cache_hit(self):
        key_hash = 'a' * 64
        reply = 'some cached response'
        source = 'node-b'
        data = build_cache_hit(key_hash, reply, source)
        parsed_hash, parsed_reply, parsed_source = parse_cache_hit(data)
        assert parsed_hash == key_hash
        assert parsed_reply == reply
        assert parsed_source == source

    def test_build_cache_hit_multiline(self):
        key_hash = 'b' * 64
        reply = 'line 1\nline 2\nline 3'
        source = 'node-a'
        data = build_cache_hit(key_hash, reply, source)
        parsed_hash, parsed_reply, parsed_source = parse_cache_hit(data)
        assert parsed_hash == key_hash
        assert parsed_reply == reply
        assert parsed_source == source

    def test_build_cache_miss(self):
        key_hash = 'c' * 64
        data = build_cache_miss(key_hash)
        assert data == key_hash.encode('ascii')

    def test_protocol_version_in_header(self):
        from common.crypto import decrypt_message
        encoded = encode_message(MESSAGE_TYPES['CACHE_GET'], b'data', TEST_KEY, 1)
        length = int.from_bytes(encoded[:4], 'big')
        pt, _ = decrypt_message(TEST_KEY, encoded[4:4+length])
        version = pt[0]
        assert version == 1
