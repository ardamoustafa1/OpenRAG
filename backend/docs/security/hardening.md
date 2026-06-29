# Application Security Hardening Checklist

This document details the mandatory security hardening configurations required for the Enterprise AI Platform.

## A) Network Security
| Item | What is done? | Why? | Verification |
|------|---------------|------|--------------|
| **NetworkPolicy** | Restricts Pod-to-Pod communication (e.g., Frontend can only talk to Backend, Backend to DB). | Prevents lateral movement if a pod is compromised. | `kubectl describe networkpolicy` |
| **Traefik Headers** | HSTS, CSP, X-Frame-Options, X-Content-Type-Options are enforced at the Ingress level. | Mitigates XSS, Clickjacking, and MIME-sniffing attacks. | curl/browser developer tools |
| **TLS 1.3** | Enforces TLS 1.3, dropping 1.2 and below. | Deprecated ciphers are vulnerable. | `nmap --script ssl-enum-ciphers` |
| **mTLS** | Service mesh encrypts all internal traffic. | Zero Trust architecture. | Istio/Linkerd metrics |

## B) Identity & Access Management
| Item | What is done? | Why? | Verification |
|------|---------------|------|--------------|
| **Password Policy** | Min 12 chars + Pwned Passwords API check. | Prevents credential stuffing. | Try creating weak password |
| **MFA** | TOTP requirement via NextAuth. | Defends against stolen credentials. | Login flow testing |
| **Session Limits** | 15 min idle timeout + concurrent session limits. | Reduces window of opportunity for hijacked sessions. | JWT expiration checks |

## C) Data Protection
| Item | What is done? | Why? | Verification |
|------|---------------|------|--------------|
| **Encryption at Rest** | PostgreSQL Disk encryption (AES-256-GCM) + MinIO SSE-S3. | Protects against physical theft. | Cloud Provider / Storage configs |
| **PII Masking** | Structlog sanitizes emails, names, API keys before disk write. | GDPR/KVKK compliance. | Check stdout/file logs |

## D) API Security
| Item | What is done? | Why? | Verification |
|------|---------------|------|--------------|
| **Input Validation** | Strict Pydantic V2 schemas. | Prevents malformed payloads & buffer overflows. | Fuzzing APIs |
| **SQLi Protection** | SQLAlchemy ORM bindings. | Mitigates SQL Injection. | Pentesting / SQLMap |
| **File Uploads** | Magic byte checking + MIME type validation. | Prevents malicious shell uploads. | Upload test payloads |
