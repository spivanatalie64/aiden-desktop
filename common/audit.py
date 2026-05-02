import hashlib
import hmac
import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AUDIT_FACILITY = 'local6'

_audit_logger = logging.getLogger('aiden.audit')
_hash_chain: list[dict] = []
_chain_key: Optional[bytes] = None
_last_hash: Optional[str] = None


def init_audit(audit_dir: Optional[Path] = None, hmac_key: Optional[bytes] = None):
    global _chain_key, _last_hash
    _chain_key = hmac_key or hashlib.sha256(b'aiden-audit-v1').digest()
    _last_hash = None

    handler = logging.handlers.SysLogHandler(
        address='/dev/log',
        facility=logging.handlers.SysLogHandler.LOG_LOCAL6,
    ) if sys.platform == 'linux' else logging.StreamHandler()

    handler.setFormatter(logging.Formatter(
        'AIDEN[%(process)d]: %(message)s'
    ))
    _audit_logger.addHandler(handler)
    _audit_logger.setLevel(logging.INFO)


def _hash_entry(entry: dict) -> str:
    raw = json.dumps(entry, sort_keys=True, default=str).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _chain_entry(entry: dict) -> dict:
    global _last_hash
    entry['prev_hash'] = _last_hash or 'GENESIS'
    entry_hash = _hash_entry(entry)
    entry['entry_hash'] = entry_hash
    if _chain_key:
        entry['hmac'] = hmac.new(
            _chain_key,
            entry_hash.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
    _last_hash = entry_hash
    _hash_chain.append(entry)
    return entry


def emit(event: str, **fields):
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': event,
    }
    entry.update(fields)

    entry = _chain_entry(entry)

    parts = [f'{k}={v}' for k, v in entry.items()
             if k not in ('prev_hash', 'entry_hash', 'hmac')]
    _audit_logger.info(' '.join(parts))


def emit_code_exec(user: str, session: str, lang: str, code_hash: str,
                   approved: bool, sandbox: str, exit_code: int, mode: str):
    emit(
        event='code_execution',
        user=user,
        session=session,
        lang=lang,
        code_hash=code_hash,
        approved=approved,
        sandbox=sandbox,
        exit_code=exit_code,
        mode=mode,
    )


def emit_privileged(user: str, action: str, status: str, details: str = ''):
    emit(
        event='privileged',
        user=user,
        action=action,
        status=status,
        details=details,
    )


def emit_settings_change(user: str, key: str):
    emit(
        event='settings_change',
        user=user,
        key=key,
    )


def emit_mesh(user: str, action: str, peer: str, status: str):
    emit(
        event='mesh',
        user=user,
        action=action,
        peer=peer,
        status=status,
    )


def emit_auth(user: str, status: str, method: str = 'ssh'):
    emit(
        event='auth',
        user=user,
        status=status,
        method=method,
    )


def get_chain() -> list[dict]:
    return _hash_chain.copy()
