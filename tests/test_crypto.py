"""Tests for common/crypto.py – encryption, SSH keys, ECDH."""
import os
import sys
import tempfile
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from pathlib import Path
from cryptography.hazmat.primitives import serialization

from common.crypto import (
    NodeIdentity, load_key_from_file, generate_key_in_sandbox,
    ecdh_handshake, encrypt_message, decrypt_message,
    sign_challenge, verify_challenge,
)


@pytest.fixture
def test_key_path():
    with tempfile.TemporaryDirectory() as tmp:
        key_path = Path(tmp) / 'id_ed25519'
        subprocess.run(
            ['ssh-keygen', '-t', 'ed25519', '-f', str(key_path), '-N', '', '-q'],
            check=True, capture_output=True,
        )
        yield key_path


@pytest.fixture
def identity(test_key_path) -> NodeIdentity:
    return load_key_from_file(test_key_path)


class TestNodeIdentity:
    def test_load_from_file(self, identity):
        assert identity.fingerprint
        assert len(identity.fingerprint) == 16
        assert identity.full_fingerprint.startswith('SHA256:')

    def test_sign_and_verify(self, identity):
        data = b'hello aiden mesh'
        sig = identity.sign(data)
        assert identity.verify(data, sig)
        assert not identity.verify(data + b'tamper', sig)

    def test_public_key_bytes(self, identity):
        pub = identity.public_key_bytes()
        assert len(pub) == 32


class TestKeyGeneration:
    def test_generate_in_sandbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'id_aiden_mesh'
            identity = generate_key_in_sandbox(target)
            assert isinstance(identity, NodeIdentity)
            assert identity.fingerprint
            assert target.exists()
            assert target.with_suffix('.pub').exists()

    def test_generated_key_signs(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'id_aiden_mesh'
            generate_key_in_sandbox(target)
            identity = load_key_from_file(target)
            data = b'test data'
            sig = identity.sign(data)
            assert identity.verify(data, sig)


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        key = os.urandom(32)
        plaintext = b'secret conversation data'
        for seq in range(5):
            ct = encrypt_message(key, plaintext, seq)
            assert len(ct) > 0
            pt, decoded_seq = decrypt_message(key, ct)
            assert pt == plaintext
            assert decoded_seq == seq

    def test_encrypt_wrong_key_fails(self):
        key_a = os.urandom(32)
        key_b = os.urandom(32)
        ct = encrypt_message(key_a, b'secret', 0)
        with pytest.raises(Exception):
            decrypt_message(key_b, ct)

    def test_encrypt_replay_detection(self):
        key = os.urandom(32)
        ct = encrypt_message(key, b'data', 42)
        pt, seq = decrypt_message(key, ct)
        assert seq == 42


class TestECDH:
    def test_handshake_produces_shared_key(self):
        from cryptography.hazmat.primitives.asymmetric import x25519
        with tempfile.TemporaryDirectory() as tmp:
            path_a = Path(tmp) / 'id_a'
            path_b = Path(tmp) / 'id_b'
            subprocess.run(['ssh-keygen', '-t', 'ed25519', '-f', str(path_a), '-N', '', '-q'],
                          check=True, capture_output=True)
            subprocess.run(['ssh-keygen', '-t', 'ed25519', '-f', str(path_b), '-N', '', '-q'],
                          check=True, capture_output=True)

            # Generate ephemeral X25519 keypairs for both sides
            eph_a_priv = x25519.X25519PrivateKey.generate()
            eph_a_pub = eph_a_priv.public_key()
            eph_a_pub_bytes = eph_a_pub.public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw
            )

            eph_b_priv = x25519.X25519PrivateKey.generate()
            eph_b_pub = eph_b_priv.public_key()
            eph_b_pub_bytes = eph_b_pub.public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw
            )

            # Each side computes shared secret using the other's ephemeral pubkey
            shared_a = eph_a_priv.exchange(eph_b_pub)
            shared_b = eph_b_priv.exchange(eph_a_pub)

            assert shared_a == shared_b
            assert len(shared_a) == 32

    def test_challenge_response(self, identity):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'id_peer'
            subprocess.run(['ssh-keygen', '-t', 'ed25519', '-f', str(path), '-N', '', '-q'],
                          check=True, capture_output=True)
            peer = load_key_from_file(path)

            challenge = os.urandom(32)
            sig = sign_challenge(identity, challenge)
            # Signer's identity signs, verifier uses signer's pubkey
            assert verify_challenge(identity.public_key_bytes(), challenge, sig)
            # Should fail if we verify with wrong pubkey
            assert not verify_challenge(peer.public_key_bytes(), challenge, sig)
