#!/usr/bin/env python3
"""Minimal privileged helper for AIDEN.

This script is a scaffold: it demonstrates how to expose limited privileged
operations. It MUST be installed by a package manager to a system path and be
invoked via polkit (pkexec) or a systemd service with appropriate policy.

Do not enable this un-reviewed; only add the specific operations you need.
"""
import argparse
import subprocess
import sys
import logging

"""Hardened privileged helper.

Only allows specific actions. For 'run' action, commands must match an explicit
whitelist. This script should be installed with root ownership and executed via
pkexec or another polkit mechanism.
"""

import json
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

# This path should be configured by the package installer, pointing to where
# the encrypted whitelist is placed (e.g., /etc/aiden/whitelist.enc)
ENCRYPTED_WHITELIST_PATH = '/etc/aiden/whitelist.enc'
DEFAULT_WHITELIST_PATH = Path(__file__).parent / 'whitelist.enc'


def derive_key(password: str, salt: bytes, iterations: int = 200_000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    return kdf.derive(password.encode('utf-8'))


def load_and_decrypt_whitelist(password: str):
    """Loads and decrypts the command whitelist."""
    path = Path(ENCRYPTED_WHITELIST_PATH)
    if not path.exists():
        # Fallback for development/testing
        path = DEFAULT_WHITELIST_PATH
        if not path.exists():
             raise FileNotFoundError("Encrypted whitelist not found.")

    with open(path, 'r', encoding='utf-8') as f:
        payload = json.load(f)

    salt = base64.b64decode(payload['salt'])
    nonce = base64.b64decode(payload['nonce'])
    ct = base64.b64decode(payload['ct'])

    key = derive_key(password, salt)
    aes = AESGCM(key)
    pt = aes.decrypt(nonce, ct, None).decode('utf-8')
    
    j = json.loads(pt)
    allowed = j.get('allowed', [])
    res = []
    for item in allowed:
        if isinstance(item, list) and all(isinstance(t, str) for t in item):
            res.append(item)
    return res


def reboot_system():
    subprocess.check_call(['systemctl', 'reboot'])


def is_allowed(cmd_list, allowed_cmds):
    for allowed in allowed_cmds:
        if cmd_list == allowed:
            return True
    return False


def run_command(cmd, allowed_cmds):
    if not is_allowed(cmd, allowed_cmds):
        raise PermissionError('command not permitted')
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')


def main():
    logging.basicConfig(level=logging.INFO)
    
    password = os.environ.get('AIDEN_WHITELIST_KEY')
    if not password:
        print('CRITICAL: AIDEN_WHITELIST_KEY is not set. Cannot operate securely.', file=sys.stderr)
        sys.exit(10)

    try:
        allowed_cmds = load_and_decrypt_whitelist(password)
    except Exception as e:
        print(f'CRITICAL: Failed to load or decrypt whitelist: {e}', file=sys.stderr)
        sys.exit(11)

    parser = argparse.ArgumentParser()
    parser.add_argument('--action', required=True, choices=['reboot', 'run'])
    parser.add_argument('--cmd', nargs='+')
    args = parser.parse_args()

    try:
        if args.action == 'reboot':
            logging.info('Performing reboot')
            reboot_system()
            print('rebooting')
            return

        if args.action == 'run':
            if not args.cmd:
                print('missing --cmd', file=sys.stderr)
                sys.exit(2)
            out = run_command(args.cmd, allowed_cmds)
            print(out)
    except PermissionError as e:
        print(f'Permission denied: {e}', file=sys.stderr)
        sys.exit(3)
    except subprocess.CalledProcessError as e:
        print(e.output.decode('utf-8', errors='ignore'), file=sys.stderr)
        sys.exit(e.returncode)


if __name__ == '__main__':
    main()
