import os
import json
from pathlib import Path
from typing import List

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import secrets

DEFAULT_DIR = Path.home() / '.local' / 'share' / 'aiden'


def ensure_dirs(base: Path = DEFAULT_DIR):
    (base / 'conversations').mkdir(parents=True, exist_ok=True)
    (base / 'meta').mkdir(parents=True, exist_ok=True)


def derive_key(password: str, salt: bytes, iterations: int = 200_000) -> bytes:
    # PBKDF2 to derive 32-byte key for AES-GCM
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    return kdf.derive(password.encode('utf-8'))


def new_conversation_id() -> str:
    return secrets.token_hex(12)


def encrypt_and_store(text: str, password: str, convo_id: str = None, base: Path = DEFAULT_DIR) -> str:
    """Encrypts text and writes to a file. Returns convo_id."""
    ensure_dirs(base)
    if convo_id is None:
        convo_id = new_conversation_id()
    salt = secrets.token_bytes(16)
    key = derive_key(password, salt)
    aes = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aes.encrypt(nonce, text.encode('utf-8'), None)

    payload = {
        'salt': base64.b64encode(salt).decode('ascii'),
        'nonce': base64.b64encode(nonce).decode('ascii'),
        'ct': base64.b64encode(ct).decode('ascii'),
    }
    path = base / 'conversations' / f'{convo_id}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f)
    return convo_id


def decrypt_conversation(convo_id: str, password: str, base: Path = DEFAULT_DIR) -> str:
    path = base / 'conversations' / f'{convo_id}.json'
    with open(path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    salt = base64.b64decode(payload['salt'])
    nonce = base64.b64decode(payload['nonce'])
    ct = base64.b64decode(payload['ct'])
    key = derive_key(password, salt)
    aes = AESGCM(key)
    pt = aes.decrypt(nonce, ct, None)
    return pt.decode('utf-8')


def list_conversations(base: Path = DEFAULT_DIR) -> List[str]:
    p = base / 'conversations'
    if not p.exists():
        return []
    return [f.stem for f in p.iterdir() if f.suffix == '.json']


def search_snippets(query: str, password: str, max_chars: int = 800, base: Path = DEFAULT_DIR) -> List[str]:
    """Return short snippets.

    This function uses a small TF-IDF style scoring implemented without
    external dependencies for better relevance. It keeps total characters
    <= max_chars.
    """
    # tokenize
    def tokenize(s: str):
        return [w for w in ''.join(ch if ch.isalnum() else ' ' for ch in s).lower().split() if len(w) > 2]

    q_tokens = tokenize(query)
    if not q_tokens:
        return []

    docs = []  # tuples (cid, line)
    for cid in list_conversations(base):
        try:
            text = decrypt_conversation(cid, password, base)
        except Exception:
            continue
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for ln in lines:
            docs.append((cid, ln))

    if not docs:
        return []

    # build vocab and document term frequencies
    import math
    vocab = {}
    df = {}
    doc_tfs = []
    for cid, ln in docs:
        toks = tokenize(ln)
        tf = {}
        for t in toks:
            idx = vocab.setdefault(t, len(vocab))
            tf[t] = tf.get(t, 0) + 1
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
        doc_tfs.append(tf)

    N = len(docs)
    idf = {t: math.log((N + 1) / (1 + df.get(t, 0))) + 1.0 for t in vocab}

    # query tf
    q_tf = {}
    for t in q_tokens:
        if t in vocab:
            q_tf[t] = q_tf.get(t, 0) + 1

    # compute query vector norm
    q_vec = {t: (q_tf[t] * idf.get(t, 0)) for t in q_tf}
    q_norm = math.sqrt(sum(v * v for v in q_vec.values()))
    if q_norm == 0:
        return []

    # score documents by cosine similarity
    scored = []
    for i, (cid, ln) in enumerate(docs):
        tf = doc_tfs[i]
        dot = 0.0
        for t, qv in q_vec.items():
            dot += qv * (tf.get(t, 0) * idf.get(t, 0))
        doc_norm = math.sqrt(sum((tf.get(t, 0) * idf.get(t, 0)) ** 2 for t in tf))
        if doc_norm == 0:
            score = 0.0
        else:
            score = dot / (q_norm * doc_norm)
        if score > 0:
            scored.append((score, ln))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    total = 0
    for score, s in scored:
        if total + len(s) > max_chars:
            remaining = max_chars - total
            if remaining > 0:
                out.append(s[:remaining])
            break
        out.append(s)
        total += len(s)
    return out
