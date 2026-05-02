# Threat Model – AIDEN Desktop v1.0

## DFD (Data Flow Diagram) Overview

```
User ──▶ Tauri/TUI ──▶ Python Backend ──▶ OpenRouter Proxy ──▶ AI Model
                         │     ▲
                         ▼     │
                     Bubblewrap │
                     Sandbox    │
                         │     │
                         ▼     │
                     Subprocess │
                         │     │
                         ▼     │
                     Output ───┘
                         
Python Backend ◄──► Mesh (LAN peers)
                         via SSH auth + AES-256-GCM
```

## Threat Enumeration

### T1 – Prompt Injection (OWASP LLM-01)

**Risk:** High  
**Likelihood:** Medium  

Attacker crafts input that causes the model to generate harmful code, which the user then executes.

**Mitigation:**
1. System prompt in every preset warns the model not to trust user-provided content as instructions
2. Code execution always requires explicit user confirmation (per mode setting)
3. Sandbox limits blast radius even if code runs
4. Audit trail records every execution with code hash

**Test:** Verify that known prompt injection patterns (DAN, role-play as system, etc.) do not result in auto-execution of harmful commands.

### T2 – Sandbox Escape

**Risk:** Medium  
**Likelihood:** Low  

Attacker crafts code that escapes the Bubblewrap sandbox to gain host access.

**Mitigation:**
1. Seccomp BPF filter blocks mount, ptrace, socket creation
2. SELinux `aiden_sandbox_t` domain has no network, no write to host filesystem
3. Timeout kills runaway processes
4. Bubblewrap runs with `--die-with-parent` and `--unshare-net`

**Test:**
1. Attempt `mount` inside sandbox → should fail
2. Attempt `ptrace` → should fail  
3. Attempt network connect → should fail
4. Attempt writing outside `/tmp` → should fail

### T3 – Rogue Mesh Node

**Risk:** Medium  
**Likelihood:** Medium  

Attacker on the LAN impersonates a legitimate node to access cached conversations.

**Mitigation:**
1. Mutual SSH key challenge-response authentication
2. Each node must explicitly accept peers (not automatic)
3. Rejected peers are blocked and cannot re-announce
4. AES-256-GCM encrypted channel between nodes
5. Sequence numbers prevent replay

**Test:**
1. Present fake SSH key → should be rejected
2. Replay captured handshake → should fail (sequence number mismatch)
3. Connect without accept → should be blocked

### T4 – Audit Trail Tampering

**Risk:** Low  
**Likelihood:** Low  

Attacker modifies audit logs to hide malicious activity.

**Mitigation:**
1. Hash chain links each entry to previous (SHA-256)
2. HMAC-SHA512 per-entry integrity tag (keyed, ephemeral per session)
3. syslog ships to LOCAL6 facility (can be forwarded off-host)
4. SELinux: audit directory is append-only (no unlink)

**Test:**
1. Modify a log entry → hash chain breaks (detectable on export)
2. Delete audit file → SELinux denies

### T5 – Compromised Proxy

**Risk:** High  
**Likelihood:** Low  

The OpenRouter proxy returns malicious responses that trick the user/model.

**Mitigation:**
1. Proxy URL is user-configurable (can point to local proxy)
2. All code from model must pass through sandbox
3. User must approve every execution (click-to-run mode)
4. Developer menu allows adding alternative providers

### T6 – SSH Key Theft

**Risk:** Medium  
**Likelihood:** Low  

Attacker gains access to the in-memory SSH key.

**Mitigation:**
1. Key held only in Python backend process memory, never written to disk
2. If `ssh-agent` is present, key never enters the process at all (delegated signing)
3. On app exit, key is cleared from memory
4. Process is confined by SELinux `aiden_t` domain

### T7 – Privilege Escalation via Helper

**Risk:** Medium  
**Likelihood:** Low  

Attacker uses the polkit helper to run arbitrary commands as root.

**Mitigation:**
1. Command whitelist in `/etc/aiden/whitelist.json` (root-owned, read-only to app)
2. SELinux `aiden_helper_t` domain restricts helper to exact allowed commands
3. Helper is invoked only via `pkexec` (requires admin auth)
4. Every invocation is audited

## Risk Matrix

| Threat | Impact | Likelihood | Risk | Mitigation confidence |
|--------|--------|------------|------|----------------------|
| T1 – Prompt injection | High | Medium | High | Medium (human-in-loop) |
| T2 – Sandbox escape | High | Low | Medium | High (defense in depth) |
| T3 – Rogue node | Medium | Medium | Medium | High (crypto + acceptance) |
| T4 – Audit tampering | Low | Low | Low | High (hash chain + syslog) |
| T5 – Compromised proxy | High | Low | Medium | Medium (user approval) |
| T6 – SSH key theft | High | Low | Medium | High (agent delegation) |
| T7 – Priv esc via helper | High | Low | Medium | High (whitelist + SELinux) |

## Security Testing Plan

| Test | Type | Frequency |
|------|------|-----------|
| Prompt injection suite | Fuzzing / manual | Per release |
| Sandbox escape attempts | Automated (CI) | Per commit |
| Mesh auth replay | Automated (CI) | Per commit |
| Audit chain integrity | Automated (CI) | Per commit |
| Bubblewrap seccomp bypass | Manual pentest | Per major release |
| SELinux policy review | Manual | Per release |
| Dependency vuln scan (pip-audit) | Automated | Per commit |
| SAST (bandit, semgrep) | Automated | Per commit |
