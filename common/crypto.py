import os
import sys
import socket
import struct
import base64
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from cryptography.hazmat.primitives.asymmetric import ed25519, ec, rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.backends import default_backend

# SSH agent protocol constants
SSH_AGENTC_REQUEST_IDENTITIES = 11
SSH_AGENT_IDENTITIES_ANSWER = 12
SSH_AGENTC_SIGN_REQUEST = 13
SSH_AGENT_SIGN_RESPONSE = 14
SSH_AGENT_FAILURE = 5

SSH_KEY_TYPES = {
    'ed25519': (ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey),
}


class SSHKeyError(Exception):
    pass


class NodeIdentity:
    def __init__(self, private_key: ed25519.Ed25519PrivateKey):
        self._private_key = private_key
        self._public_key = private_key.public_key()
        pub_bytes = self._public_key.public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw
        )
        import hashlib
        self.fingerprint = hashlib.sha256(pub_bytes).hexdigest()[:16]
        self.full_fingerprint = 'SHA256:' + base64.b64encode(
            hashlib.sha256(pub_bytes).digest()
        ).decode('ascii').rstrip('=')

    def sign(self, data: bytes) -> bytes:
        return self._private_key.sign(data)

    def verify(self, data: bytes, signature: bytes) -> bool:
        try:
            self._public_key.verify(signature, data)
            return True
        except Exception:
            return False

    @classmethod
    def _from_public(cls, pub: ed25519.Ed25519PublicKey) -> 'NodeIdentity':
        node = cls.__new__(cls)
        node._private_key = None
        node._public_key = pub
        pub_bytes = pub.public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw
        )
        import hashlib
        node.fingerprint = hashlib.sha256(pub_bytes).hexdigest()[:16]
        node.full_fingerprint = 'SHA256:' + base64.b64encode(
            hashlib.sha256(pub_bytes).digest()
        ).decode('ascii').rstrip('=')
        return node

    def public_key_bytes(self) -> bytes:
        return self._public_key.public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw
        )


def discover_ssh_keys() -> list[Path]:
    ssh_dir = Path.home() / '.ssh'
    if not ssh_dir.exists():
        return []
    candidates = []
    for pattern in ['id_ed25519', 'id_ecdsa', 'id_rsa']:
        p = ssh_dir / pattern
        if p.exists():
            candidates.append(p)
    return candidates


def load_key_from_agent() -> Optional[NodeIdentity]:
    sock_path = os.environ.get('SSH_AUTH_SOCK')
    if not sock_path:
        return None
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(sock_path)
        sock.settimeout(5.0)

        identities = _agent_request_identities(sock)
        if not identities:
            sock.close()
            return None

        for key_blob, comment in identities:
            key_type = _parse_key_type(key_blob)
            if key_type == 'ssh-ed25519':
                result = _agent_sign_challenge(sock, key_blob)
                sock.close()
                if result:
                    raw_key = _extract_ed25519_raw(key_blob)
                    priv = ed25519.Ed25519PrivateKey.from_private_bytes(
                        b'\x00' * 32
                    )
                    pub = ed25519.Ed25519PublicKey.from_public_bytes(raw_key)
                    return NodeIdentity._from_public(pub)
        sock.close()
    except Exception:
        pass
    return None


def load_key_from_file(path: Path, passphrase: Optional[str] = None) -> NodeIdentity:
    try:
        with open(path, 'rb') as f:
            key_data = f.read()
    except OSError as e:
        raise SSHKeyError(f'Cannot read key file: {e}')

    try:
        if passphrase:
            priv = serialization.load_ssh_private_key(
                key_data, password=passphrase.encode('utf-8'),
                backend=default_backend()
            )
        else:
            priv = serialization.load_ssh_private_key(
                key_data, password=None,
                backend=default_backend()
            )
    except Exception as e:
        raise SSHKeyError(f'Failed to load key: {e}')

    if not isinstance(priv, ed25519.Ed25519PrivateKey):
        raise SSHKeyError('Only Ed25519 keys are supported')

    node = NodeIdentity.__new__(NodeIdentity)
    node._private_key = priv
    node._public_key = priv.public_key()
    pub_bytes = node._public_key.public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw
    )
    import hashlib
    node.fingerprint = hashlib.sha256(pub_bytes).hexdigest()[:16]
    node.full_fingerprint = 'SHA256:' + base64.b64encode(
        hashlib.sha256(pub_bytes).digest()
    ).decode('ascii').rstrip('=')
    return node


def generate_key_in_sandbox(target_path: Path) -> NodeIdentity:
    temp_dir = tempfile.mkdtemp(prefix='aiden-keygen-')
    key_path = Path(temp_dir) / 'id_aiden_mesh'
    try:
        subprocess.run(
            ['ssh-keygen', '-t', 'ed25519', '-f', str(key_path), '-N', '', '-q'],
            check=True, capture_output=True, timeout=30
        )
        subprocess.run(
            ['cp', str(key_path), str(target_path)],
            check=True, capture_output=True, timeout=10
        )
        subprocess.run(
            ['cp', str(key_path) + '.pub', str(target_path) + '.pub'],
            check=True, capture_output=True, timeout=10
        )
        os.chmod(target_path, 0o600)
        return load_key_from_file(target_path)
    except subprocess.CalledProcessError as e:
        raise SSHKeyError(f'Key generation failed: {e.stderr.decode()}')
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def generate_key_interactive(target_path: Path) -> NodeIdentity:
    return generate_key_in_sandbox(target_path)


def ecdh_handshake(identity: NodeIdentity, peer_pubkey_raw: bytes) -> Tuple[bytes, bytes]:
    our_eph = x25519.X25519PrivateKey.generate()
    our_eph_pub = our_eph.public_key()
    our_eph_pub_bytes = our_eph_pub.public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw
    )

    peer_eph_pub = x25519.X25519PublicKey.from_public_bytes(peer_pubkey_raw)
    shared = our_eph.exchange(peer_eph_pub)

    session_key = HKDF(
        algorithm=hashes.SHA512(),
        length=32,
        salt=None,
        info=b'aiden-lan-v1',
        backend=default_backend()
    ).derive(shared)

    return session_key, our_eph_pub_bytes


def encrypt_message(key: bytes, plaintext: bytes, seq: int) -> bytes:
    aes = AESGCM(key)
    nonce = seq.to_bytes(12, 'big')
    ct = aes.encrypt(nonce, plaintext, None)
    return nonce + ct


def decrypt_message(key: bytes, ciphertext: bytes) -> Tuple[bytes, int]:
    nonce = ciphertext[:12]
    seq = int.from_bytes(nonce, 'big')
    aes = AESGCM(key)
    pt = aes.decrypt(nonce, ciphertext[12:], None)
    return pt, seq


def sign_challenge(identity: NodeIdentity, challenge: bytes) -> bytes:
    return identity.sign(challenge)


def verify_challenge(peer_pubkey_raw: bytes, challenge: bytes, signature: bytes) -> bool:
    try:
        pub = ed25519.Ed25519PublicKey.from_public_bytes(peer_pubkey_raw)
        pub.verify(signature, challenge)
        return True
    except Exception:
        return False


def _agent_request_identities(sock: socket.socket) -> list[Tuple[bytes, str]]:
    _agent_send(sock, SSH_AGENTC_REQUEST_IDENTITIES, b'')
    resp_type, data = _agent_recv(sock)
    if resp_type != SSH_AGENT_IDENTITIES_ANSWER:
        return []
    n = struct.unpack('>I', data[:4])[0]
    pos = 4
    identities = []
    for _ in range(n):
        klen = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4
        key_blob = data[pos:pos+klen]
        pos += klen
        clen = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4
        comment = data[pos:pos+clen].decode('utf-8', errors='replace')
        pos += clen
        identities.append((key_blob, comment))
    return identities


def _agent_sign_challenge(sock: socket.socket, key_blob: bytes) -> Optional[bytes]:
    challenge = os.urandom(32)
    req = struct.pack('>I', len(key_blob)) + key_blob
    req += struct.pack('>I', len(challenge)) + challenge
    req += struct.pack('>I', 0)
    _agent_send(sock, SSH_AGENTC_SIGN_REQUEST, req)
    resp_type, data = _agent_recv(sock)
    if resp_type == SSH_AGENT_SIGN_RESPONSE:
        slen = struct.unpack('>I', data[:4])[0]
        return data[4:4+slen]
    return None


def _agent_send(sock: socket.socket, msg_type: int, data: bytes):
    payload = struct.pack('B', msg_type) + data
    packet = struct.pack('>I', len(payload)) + payload
    sock.sendall(packet)


def _agent_recv(sock: socket.socket) -> Tuple[int, bytes]:
    header = sock.recv(4)
    length = struct.unpack('>I', header)[0]
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            break
        data += chunk
    if not data:
        return SSH_AGENT_FAILURE, b''
    return data[0], data[1:]


def _parse_key_type(key_blob: bytes) -> str:
    klen = struct.unpack('>I', key_blob[:4])[0]
    return key_blob[4:4+klen].decode('ascii')


def _extract_ed25519_raw(key_blob: bytes) -> bytes:
    pos = 4
    klen = struct.unpack('>I', key_blob[pos:pos+4])[0]
    pos += 4 + klen
    pklen = struct.unpack('>I', key_blob[pos:pos+4])[0]
    pos += 4
    return key_blob[pos:pos+pklen]
