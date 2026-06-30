# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported | End of Support |
| ------- | --------- | -------------- |
| `main` / `latest` | ✅ Active | Ongoing |
| `>= 0.1.x` | ✅ Active | Until v0.3.0 released |
| `< 0.1.0` | ❌ End of Life | — |

> **Enterprise customers** on a support contract receive extended patch support. Contact `enterprise@openrag.com` for details.

---

## Reporting a Vulnerability

Security is a top priority for the Enterprise RAG AI Platform. We take all security reports seriously.

### ❗ Please DO NOT report security vulnerabilities via public GitHub Issues.

### 🔒 Private Disclosure (Preferred)

Use [GitHub's private vulnerability reporting](https://github.com/ardamoustafa1/OpenRAG/security/advisories/new) to submit a report directly to the maintainers confidentially.

### 📧 Email Disclosure

Alternatively, send an email to **`security@openrag.com`** with:

1. A **clear description** of the vulnerability.
2. **Steps to reproduce** (including any PoC code or payloads).
3. **Potential impact** (what an attacker could achieve).
4. Your **preferred credit** (name/handle for acknowledgment, or anonymous).

Encrypt sensitive reports using our [PGP key](https://keys.openpgp.org/search?q=security%40openrag.com) if needed.

---

## Response SLA

| Stage | Target |
|-------|--------|
| **Acknowledgment** | Within 48 hours |
| **Initial triage** | Within 5 business days |
| **Fix development** (critical/high) | Within 14 days |
| **Fix development** (medium/low) | Within 30 days |
| **Public disclosure** | Coordinated with reporter |

---

## Severity Classification

We classify issues using the [CVSS v3.1](https://www.first.org/cvss/calculator/3.1) scoring system:

| Severity | CVSS Score | Examples |
|----------|-----------|---------|
| **Critical** | 9.0–10.0 | RCE, auth bypass, tenant data leak |
| **High** | 7.0–8.9 | Privilege escalation, SQLi, SSRF |
| **Medium** | 4.0–6.9 | XSS, CSRF, info disclosure |
| **Low** | 0.1–3.9 | Minor info disclosure, rate limit bypass |

---

## Scope

### ✅ In Scope
- FastAPI backend (`/backend`)
- Next.js frontend (`/frontend`)
- Docker Compose infrastructure (`docker-compose.yml`)
- Helm charts (`/infra/helm`)
- Authentication flows (JWT, MFA, SAML, OIDC)
- Multi-tenant isolation mechanisms
- SDK packages (`/sdk`)

### ❌ Out of Scope
- Third-party services (Qdrant, MinIO, Ollama, LiteLLM) — report to their maintainers directly.
- Vulnerabilities in `dev` dependencies only used in testing.
- Social engineering attacks.
- DoS attacks requiring massive external resources.

---

## Security Hall of Fame

We publicly acknowledge researchers who responsibly disclose security issues. Upon resolution and public disclosure, your name/handle will be added here.

| Researcher | Vulnerability | CVE |
|-----------|--------------|-----|
| *Your name could be here* | — | — |

---

## Secure Development

This project follows these security practices:

- **Secrets**: All credentials managed via environment variables; `.env` is gitignored.
- **Hashing**: Argon2id for passwords; SHA-256 for API keys and token blacklisting.
- **Auth**: JWT with rotation + refresh token blacklisting via Redis.
- **Multi-tenancy**: Tenant context enforced at middleware level on every request.
- **Dependencies**: Automated weekly scans via `pip-audit` (Python) and `npm audit` (Node.js) in CI.
- **Container scanning**: Trivy scans all Docker images in CI — CRITICAL/HIGH CVEs block merges.
- **Static analysis**: Bandit for Python SAST on every PR.
