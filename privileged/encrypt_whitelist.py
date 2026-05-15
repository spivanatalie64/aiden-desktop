#!/usr/bin/env python3
"""Encrypts the whitelist.json file for use by the privileged helper.

This script reads a password from the AIDEN_WHITELIST_KEY environment variable,
encrypts privileged/whitelist.json, and writes the output to
privileged/whitelist.enc.
"""
import os
import json
import base64
import secrets
from pathlib import Path

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# This script should be run from the project root
ROOT_DIR = Path(__file__).parent.parent
PRIV_DIR = ROOT_DIR / 'privileged'


def derive_key(password: str, salt: bytes, iterations: int = 200_000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    return kdf.derive(password.encode('utf-8'))


def main():
    password = os.environ.get('AIDEN_WHITELIST_KEY')
    if not password:
        print('Error: AIDEN_WHITELIST_KEY environment variable not set.')
        return

    input_path = PRIV_DIR / 'whitelist.json'
    output_path = PRIV_DIR / 'whitelist.enc'

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            plaintext = f.read()
    except FileNotFoundError:
        print(f"Error: {input_path} not found.")
        return

    salt = secrets.token_bytes(16)
    key = derive_key(password, salt)
    aes = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aes.encrypt(nonce, plaintext.encode('utf-8'), None)

    payload = {
        'salt': base64.b64encode(salt).decode('ascii'),
        'nonce': base64.b64encode(nonce).decode('ascii'),
        'ct': base64.b64encode(ct).decode('ascii'),
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f)

    print(f"Successfully encrypted {input_path} to {output_path}")


if __name__ == '__main__':
    main()
