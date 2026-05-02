# Security Target – AIDEN Desktop v1.0
## Target: Common Criteria EAL2 (v1) → EAL4 (roadmap)

### 1. TOE (Target of Evaluation) Overview

**TOE Name:** AIDEN Desktop  
**TOE Version:** 1.0  
**Developer:** AcreetionOS Project  
**Type:** AI Assistant Desktop Application  

The TOE is a desktop AI assistant application providing:
- Encrypted local conversation storage
- Configurable AI model proxy access
- Sandboxed code execution on the local machine
- Privileged operation via polkit with whitelist enforcement
- LAN mesh for distributed conversation caching
- SSH-key authenticated peer discovery

### 2. Security Problem Definition

#### 2.1 Threats

| ID | Threat | Description |
|----|--------|-------------|
| T.AI | Malicious prompt injection | Attacker controls model output to generate harmful code |
| T.ESC | Privilege escalation | Unauthorized process gains elevated permissions via helper |
| T.EXFIL | Data exfiltration | Stored encrypted conversations accessed without authorization |
| T.PEER | Rogue LAN peer | Unauthorized node joins the mesh and accesses cache |
| T.SANDBOX | Sandbox escape | Code executed in sandbox breaks out to host |
| T.AUDIT | Audit tampering | Security logs modified or deleted without detection |

#### 2.2 Assumptions

| ID | Assumption |
|----|------------|
| A.OS | The underlying OS (Linux with SELinux) is correctly configured and not compromised |
| A.NET | The LAN is a trusted network; inter-node traffic is additionally encrypted |
| A.USER | The user has accepted the disclaimer and is responsible for their actions |
| A.UPDATE | Software updates are obtained from trusted sources and verified |

#### 2.3 Organizational Security Policies

- OSP.CRYPTO: All stored data must be encrypted using FIPS 140-3 approved algorithms
- OSP.AUDIT: All security-relevant events must be logged to syslog with integrity protection
- OSP.SANDBOX: All user-requested code execution must occur in a sandboxed environment
- OSP.AUTH: LAN mesh nodes must authenticate via SSH key challenge-response

### 3. Security Functional Requirements (SFRs)

#### FAU_GEN.1 – Audit Data Generation

The TOE shall generate audit records for:
- Code execution (with mode, sandbox type, exit code)
- Privileged actions (via polkit helper)
- Settings changes
- Mesh peer authentication (accept/reject)
- Authentication events
- Denial events (disclaimer not accepted)

Format: syslog LOCAL6 with structured key=value pairs.

#### FCS_CKM.1 – Cryptographic Key Generation

The TOE shall use:
- Ed25519 for SSH key-based node authentication
- X25519 ECDH for per-session key exchange
- HKDF-SHA512 for key derivation
- AES-256-GCM for data encryption

#### FCS_COP.1 – Cryptographic Operation

The TOE shall implement:
- AES-256-GCM encryption/decryption (FIPS 140-3)
- HMAC-SHA512 message integrity (FIPS 198-1)
- SHA-256/SHA-512 hashing (FIPS 180-4)

#### FDP_ACC.1 – Subset Access Control

The TOE enforces:
- SELinux domain transitions: aiden_t → helper_t (via pkexec only)
- SELinux domain transitions: aiden_t → sandbox_t (via bubblewrap only)
- Code execution whitelist (no network, no mount, no ptrace in sandbox)
- Polkit helper command whitelist

#### FIA_UAU.1 – User Authentication

The TOE authenticates LAN mesh nodes via:
- SSH key challenge-response (Ed25519)
- Mutual accept/reject with both nodes notified
- HMAC-SHA512 message integrity

#### FPT_STM.1 – Audit Trail Integrity

The TOE maintains:
- Hash chain linking audit entries (SHA-256)
- HMAC-SHA512 per-entry integrity tag
- Append-only audit log (SELinux enforced)

### 4. Security Assurance Requirements (SARs)

| SAR | Level v1 | Level v2 (roadmap) |
|-----|----------|-------------------|
| ADV_ARC.1 | Security architecture description | ADV_ARC.1 |
| ADV_FSP.1 | Functional specification | ADV_FSP.2 |
| ADV_TDS.1 | TOE design | ADV_TDS.2 |
| AGD_OPE.1 | Operational user guidance | AGD_OPE.1 |
| AGD_PRE.1 | Preparative procedures | AGD_PRE.1 |
| ALC_CMC.1 | CM capabilities | ALC_CMC.2 |
| ALC_CMS.1 | CM scope | ALC_CMS.2 |
| ATE_COV.1 | Evidence of coverage | ATE_COV.2 |
| ATE_FUN.1 | Functional testing | ATE_FUN.1 |
| ATE_IND.1 | Independent testing | ATE_IND.2 |
| AVA_VAN.1 | Vulnerability analysis | AVA_VAN.2 |

### 5. TOE Architecture

```
┌──────────────────────────────────────────────────┐
│  Application Layer                                │
│  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │ GTK    │  │ Tauri  │  │ TUI    │            │
│  │(legacy)│  │(Gecko) │  │(Textual)│           │
│  └───┬────┘  └───┬────┘  └───┬────┘            │
│      └───────────┼───────────┘                   │
│                  ▼                               │
│  ┌──────────────────────────────────────────┐   │
│  │  Python Backend (FastAPI / direct)        │   │
│  │  common/ – crypto, sandbox, audit, mesh   │   │
│  └──────┬──────┬──────┬──────────────────────┘   │
│         │      │      │                          │
│         ▼      ▼      ▼                          │
│  ┌──────┐ ┌──────┐ ┌──────┐                     │
│  │bwrap │ │pkexec│ │syslog│                     │
│  │sandbx│ │helper│ │audit │                     │
│  └──────┘ └──────┘ └──────┘                     │
│                                                   │
│  SELinux: aiden_t | helper_t | sandbox_t         │
│  Crypto:  FIPS 140-3 mode                        │
└──────────────────────────────────────────────────┘
```

### 6. EAL2 → EAL4 Roadmap

| Phase | EAL | Timeline | Key artifacts |
|-------|-----|----------|--------------|
| v1 | EAL2 | Initial release | Functional spec, user/admin guides, CM, basic testing |
| v1.5 | EAL3 | +6 months | Formal development security, structured testing, enhanced CM |
| v2 | EAL4 | +12 months | Formal security policy model, full lifecycle, comprehensive testing |
