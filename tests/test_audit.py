"""Tests for common/audit.py – syslog + hash chain."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

from common.audit import (
    init_audit, emit, emit_code_exec, emit_auth,
    get_chain,
)


class TestAuditHashChain:
    def test_chain_entries_have_hashes(self):
        init_audit(hmac_key=b'test-key')
        emit('test_event', key1='value1')
        emit('test_event', key2='value2')
        chain = get_chain()
        assert len(chain) >= 2

        for entry in chain:
            assert 'entry_hash' in entry
            assert 'prev_hash' in entry
            assert 'hmac' in entry
            assert len(entry['hmac']) == 128

    def test_chain_is_linked(self):
        init_audit(hmac_key=b'test-key')
        emit('event_a', data='first')
        emit('event_b', data='second')
        chain = get_chain()
        assert chain[-1]['prev_hash'] == chain[-2]['entry_hash']

    def test_first_entry_is_genesis(self):
        init_audit(hmac_key=b'test-key')
        emit('first_event')
        chain = get_chain()
        assert chain[-1]['prev_hash'] == 'GENESIS'


class TestAuditEvents:
    def test_code_exec_event(self):
        init_audit(hmac_key=b'test-key')
        emit_code_exec(
            user='testuser',
            session='sess_001',
            lang='python',
            code_hash='abc123',
            approved=True,
            sandbox='bubblewrap',
            exit_code=0,
            mode='click_to_run',
        )
        chain = get_chain()
        last = chain[-1]
        assert last['event'] == 'code_execution'
        assert last['user'] == 'testuser'
        assert last['lang'] == 'python'
        assert last['approved'] is True

    def test_auth_event(self):
        init_audit(hmac_key=b'test-key')
        emit_auth(user='testuser', status='success', method='ssh')
        chain = get_chain()
        assert chain[-1]['event'] == 'auth'
        assert chain[-1]['status'] == 'success'
